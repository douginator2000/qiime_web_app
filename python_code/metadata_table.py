#/bin/env python

"""
Classes to represent metadata table information
"""

__author__ = "Doug Wendel"
__copyright__ = "Copyright 2009-2010, Qiime Web Analysis"
__credits__ = ["Doug Wendel"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = ["Doug Wendel"]
__email__ = "wendel@colorado.edu"
__status__ = "Development"

from qiime_data_access import QiimeDataAccess
import csv
import re
import os

class ColumnFactory(object):
    """ Factory class for producing metadata columns
    """
    
    def __init__(self, is_invalid):
        self._is_invalid = is_invalid

    def _columnExists(self, column_name):
        found = False
        column_detail_list = QiimeDataAccess().getColumnDictionary()
        for row in column_detail_list:
            if row[0].upper() == column_name:
                found = True
                break
                      
        return found

    def _getControlledVocabs(self, column_name, datatype):
        if datatype == 'list':
            return QiimeDataAccess().getControlledVocabs(column_name)
        elif datatype == 'ontology':
            return QiimeDataAccess().getOntologies(column_name)

    def createColumn(self, column_name, datatype, length, in_dictionary):
        """ Creates a column of the right type based on the column name
        """
        _column = None
        _controlled_vocab_list = None

        # Deterine if this column is associated with a list or ontology
        if datatype == 'list' or datatype == 'ontology':
            _controlled_vocab_list = self._getControlledVocabs(column_name, datatype)
            if _controlled_vocab_list == None:
                print 'Error: No controlled vocabulary or ontology found even though column is listed as ' + datatype + '.'
                return None
        
        # Create the appropriate type of column
        if datatype == 'numeric':
            regex = '^\-*[0-9]+$|^\-*[0-9]*\.[0-9]+$'
            _column = RegExColumn(column_name, self._is_invalid, in_dictionary, regex)
        elif datatype == 'range':
            regex = '^((\-?[0-9]+)|(\-?[0-9]*\.[0-9]+))(\-((\-?[0-9]+)|(\-?[0-9]*\.[0-9]+)))?$'
            _column = RegExColumn(column_name, self._is_invalid, in_dictionary, regex)
        elif datatype == 'yn':
            regex = '^y$|^Y$|^n$|^N$'
            _column = RegExColumn(column_name, self._is_invalid, in_dictionary, regex)
        elif datatype == 'date':
            regex = '^((((((0?[13578])|(1[02]))[\-\/\s]?((0?[1-9])|([1-2][0-9])|(3[01])))|(((0?[469])|(11))[\-\/\s]?((0?[1-9])|([1-2][0-9])|(30)))|(0?2[\-\/\s]?((0?[1-9])|([1-2][0-9]))))[\-\/\s]?\d{2}(([02468][048])|([13579][26])))|(((((0?[13578])|(1[02]))[\-\/\s]?((0?[1-9])|([1-2][0-9])|(3[01])))|(((0?[469])|(11))[\-\/\s]?((0?[1-9])|([1-2][0-9])|(30)))|(0?2[\-\/\s]?((0?[1-9])|(1[0-9])|(2[0-8]))))[\-\/\s]?\d{2}(([02468][1235679])|([13579][01345789]))))(\s(((0?[1-9])|(1[0-9])|(2[0-3]))\:([0-5][0-9])((\s)|(\:([0-5][0-9])))))?$'
            _column = RegExColumn(column_name, self._is_invalid, in_dictionary, regex)
        elif datatype == 'text':
            _column = TextColumn(column_name, self._is_invalid, in_dictionary, length)
        elif datatype == 'list':
            _column = ListColumn(column_name, self._is_invalid, in_dictionary, _controlled_vocab_list)
        elif datatype == 'ontology':
            _column = OntologyColumn(column_name, self._is_invalid, in_dictionary, _controlled_vocab_list)

        return _column

class BaseColumn(object):
    """ The base class for all column types in the metadata table. This class 
    implements common functionality for all column classes.
    """
    def __init__(self, column_name, is_invalid, in_dictionary):
        # Name of this column. Should be unique in MetadataTable object
        self.column_name = column_name
        
        # Callback to notify parent of an invalid value entry
        self.is_invalid = is_invalid
        
        # List of values in this column
        self.values = []
        
        # List of invalid indicies in this column
        self._invalid_indicies = []
        
        # RegEx validation string (if applicable)
        self.reg_exp = ''
        
        # Variable to store whether or not this column exists in the column dictionary
        self._in_dictionary = in_dictionary
    
    def _addValue(self, value, data_access):
        status = 'good'
        if not self._validate(value, data_access):
            status = 'bad'
            self.is_invalid(self.column_name, len(self.values))     
        self.values.append((value, status))

class RegExColumn(BaseColumn):
    """ RegExColumn implementation of BaseColumn class
    """
    def __init__(self, column_name, is_invalid, in_dictionary, regex):
        super(RegExColumn, self).__init__(column_name, is_invalid, in_dictionary)
        self.reg_exp = regex
        
    def writeJSValidation(self):
        function_string = 'validateRegExField(this, \'%s\', \'%s\')' % (self.column_name, self.reg_exp.replace('\\', '\\\\'))
        validation_string = ' onclick="%s;" ' % (function_string)
        validation_string += ' onkeyup="%s;" ' % (function_string)
        return validation_string
        
    def _validate(self, value, data_access):
        """ return true if number, false otherwise
        """
        if re.match(self.reg_exp, value) == None:
            return False
        else:
            return True

class ListColumn(BaseColumn):
    """ List implementation of BaseColumn class
    """
    def __init__(self, column_name, is_invalid, in_dictionary, list_names):
        super(ListColumn, self).__init__(column_name, is_invalid, in_dictionary)
        self.list_names = list_names
        
    def _addValue(self, value, data_access):
        status = 'good'
        if not self._validate(value, self.list_names, data_access):
            status = 'bad'
            self.is_invalid(self.column_name, len(self.values))
        self.values.append((value, status))
        
    def writeJSValidation(self):
        function_string = 'findListTerms(this, \'%s\')' % self.column_name 
        validation_string = ' onclick="%s;" ' % (function_string)
        validation_string += ' onkeyup="%s;" ' % (function_string)
        return validation_string

    # Consider refactoring with _validateOntology()
    def _validate(self, value, list_names, data_access):
        """ returns true if value is in list designated by list_name, 
        false otherwise
        """
        for list_name in list_names:
            if data_access.validateListValue(list_name, value) > 0:
                return True
        
        # Not found in any list
        return False

class OntologyColumn(BaseColumn):
    """ Ontology implementation of BaseColumn class
    """
    def __init__(self, column_name, is_invalid, in_dictionary, ontology_names):
        super(OntologyColumn, self).__init__(column_name, is_invalid, in_dictionary)
        self.ontology_names = ontology_names

    def _addValue(self, value, data_access):
        status = 'good'
        if not self._validate(value, self.ontology_names, data_access):
            status = 'bad'
            self.is_invalid(self.column_name, len(self.values))
        self.values.append((value, status))
        
    def writeJSValidation(self):
        function_string = 'findListTerms(this, \'%s\')' % self.column_name 
        validation_string = ' onclick="%s;" ' % (function_string)
        validation_string += ' onkeyup="%s;" ' % (function_string)
        return validation_string
    
    def _validate(self, term, ontology_names, data_access):
        """ returns true if term is in ontology designated by ontology_name, 
        false otherwise 
        """
        for ontology_name in ontology_names:
            term_values = term.split(':')
            if len(term_values) != 2:
                return False
        
            if data_access.validateOntologyValue(ontology_name, term_values[1]) > 0:
                return True
        
        # Not found in any list
        return False
    
class TextColumn(BaseColumn):
    """ Text implementation of BaseColumn class
    """
    def __init__(self, column_name, is_invalid, in_dictionary, length):
        super(TextColumn, self).__init__(column_name, is_invalid, in_dictionary)
        self.maxLength = length
        
    def _validate(self, value, data_access):
        """ return true if number, false otherwise
        """
        if self.maxLength == '':
            return False
        elif len(value) > self.maxLength:
            return False
        else:
            return True
        
    def writeJSValidation(self):
        function_string = 'validateTextLength(this, \'%s\', \'%s\')' % (self.column_name, self.maxLength)
        validation_string = ' onclick="%s;" ' % (function_string)
        validation_string += ' onkeyup="%s;" ' % (function_string)
        return validation_string
        
class MetadataTable(object):
    """ Represents a metadata table object
    
    This class encapsulates the functionality of a metadata table
    for use with the Qiime database. It ties together the concept
    of a metadata file along with the validation associated with
    each type of column.
    """

    _metadataFile = None

    def __init__(self, metadataFile):
        global _metadataFile
        
        self._invalid_rows = []
        self._columns = []
        self._metadataFile = metadataFile
        try:
            self._readMetadataFile()
        except Exception, e:
            # Try to figure out what went wrong
            column_list = 'Successfully read columns: <p/>'
            for col in self._columns:
                column_list += col.column_name + '<br>'
            error_message = str(e) + '<p/>' + column_list
            raise Exception(error_message)
        
    def getInvalidRows(self):
        return self._invalid_rows
        
    def writeToDatabase(self, data_access):
        if len(self._invalid_rows) > 0:
            raise Exception('Data cannot be written while invalid rows still exist')
        else:
            data_access.writeTableToDatabase()
            
    def _is_invalid(self, column_name, invalid_row):
        """ A callback that is fired when an invalid field has been found
        """
        self._invalid_rows.append((column_name, invalid_row))

    def _readMetadataFile(self):
        global _metadataFile
        column_factory = ColumnFactory(self._is_invalid)
        data_file = open(self._metadataFile, "rU")
        reader = csv.reader(data_file,  delimiter='\t')
        data_access = QiimeDataAccess()

        # Obtain the list of metadata columns for validation
        column_detail_list = QiimeDataAccess().getColumnDictionary()
        column_details = {}
        for item in column_detail_list:
            # Store off the data type and data length for each column name
            column_details[item[0]] = (item[3], item[4])

        # Create the header columns
        headers = reader.next()
        for column in headers:
            try:    
                if column in column_details:
                    result = column_factory.createColumn(column, column_details[column][0], column_details[column][1], True)
                    if result:
                        self._addColumn(result)
                    else:
                        raise ValueError('Column creation failed for \'' + column + '\' however the column does exist in the column dictionary')
                # Column not in dictionary - was added by user. Capture this field and store as metadata
                else:
                    result = column_factory.createColumn(column, 'text', '4000', False)
                    if result:
                        self._addColumn(result)
            except Exception as err:
                raise err

        # Read the column values
        try:
            for row in reader:
                # Skip any rows starting with white space
                if len(row) == 0:
                    continue
                if row[0].startswith('\t') or row[0].startswith(' '):
                    continue
    
                # If a row is incomplete, probably means end of file whitespace
                if len(row) < len(self._columns):
                    continue
                
                i = 0
                for column in row:
                    # Some files contain extra whitespace characters beyond the bounds of the last column.
                    # Skip over these values.
                    if (i > len(self._columns) - 1):
                        continue
                    
                    # Add the current value to the appropriate metadata table column
                    self._columns[i]._addValue(column.strip(), data_access)
                    i += 1
        except Exception, e:
            msg = 'Error adding data to column %s. Maximum column index for this metadata table is %s. The error was: \n<p/>%s' % (str(i), str(len(self._columns) - 1), str(e))
            raise Exception(msg)

        #self._printTable()
        #self._printInvalidRows()

    def _addColumn(self, column):
        self._columns.append(column)

    def _printInvalidRows(self):
        print 'Invalid Rows:'
        for row in self._invalid_rows:
            print row

    """ depreciated
    def _printTable(self):
        print '\n\n'
        column_count = len(self._columns)
        row_count = len(self._columns[0].values)

        x = 0

        while x < column_count:
            print self._columns[x].column_name + '\t',
            x += 1

        y = 0
        
        while y < row_count:
            x = 0
            print '\n',
            while x < column_count:
                for column in self._columns:
                    print str(column.values[y]) + '\t',
                    x += 1
            y += 1 
            
        print '\n\n'
    """

    def printHTMLTable(self):
        # Determine the type of file we're dealing with
        file_type = ''
        if os.path.basename(self._metadataFile).startswith('study'):
            file_type = 'study'
        elif os.path.basename(self._metadataFile).startswith('sample'):
            file_type = 'sample'
        elif os.path.basename(self._metadataFile).startswith('prep'):
            file_type = 'prep'
        else:
            return
        
        html_table = '<table class="metadata_table">'
        
        column_count = len(self._columns)
        row_count = len(self._columns[0].values)

        # Print the column headers
        x = 0
        while x < column_count:
            current_column = self._columns[x]
            if current_column._in_dictionary:
                html_table += '<th class="meta_th">' + self._columns[x].column_name + '</th>\n'
            else:
                html_table += '<th class="meta_th" style="background:#00FFFF">' + self._columns[x].column_name + '</th>\n'
            x += 1
        
        #####################################
        # Print the table rows
        #####################################
        
        # Max length for text columns
        max_text_length = 50
        
        # Count of errors on page
        error_count = 0
        
        # Index for rows
        y = 0
        
        while y < row_count:
            x = 0
            html_table += '<tr>\n'
            while x < column_count:
                for column in self._columns:

                    # Create a unique column name for processing later
                    unique_column_name = file_type + ':' + str(y) + ':' + str(x) + ':' + column.column_name

                    # This is the output value for the HTML page. It may be truncated for display if the
                    # text is very long.
                    value_output = str(column.values[y][0])

                    # This will always hold the full value of the field. Used for submission to database.
                    actual_value = str(column.values[y][0])
                    
                    #For fields that are valid:
                    if column.values[y][1] == 'good':
                        # If this is a text column, truncate the length of the string to keep the display reasonable
                        if type(column) == TextColumn:
                            if len(value_output) > max_text_length:
                                value_output = value_output[:max_text_length] + '...'
                            
                        hidden_field_text = '<input type=\"hidden\" id=\"%s\" name=\"%s\" value=\"%s\">\n' % (unique_column_name, unique_column_name, actual_value)
                        cell_color = '#FFFFFF'
                        html_table += '<td style=\"background-color:%s;\">%s%s</td>\n' % (cell_color, hidden_field_text, value_output)
                    
                    # For fields that are not valid
                    else:
                        error_count += 1
                        cell_color = '#EEEEFF'
                        html_table += '<td style="background-color:#DDDDDD;"><input style="background-color:%s;" type="text" id="%s" name="%s" value="%s" %s> <br/> \
                            <a href="" onclick="replaceWithCurrent(\'%s\');return false;"><div style="font-size:11px">replace all</div></a></td>\n' \
                            % (cell_color, unique_column_name, unique_column_name, actual_value, column.writeJSValidation(), unique_column_name)
                    x += 1
                    
            html_table +='</tr>\n'
            y += 1 
        
        html_table += '</table>\n'
                
        # Form variable to hold count of errors on page. Determines when "sumbit" will be enabled.
        #html_table += '<input type="hidden" name="%s_error_count" value="%s"\n' % (file_type, error_count)
        
        return html_table, error_count
