create or replace procedure ag_insert_barcode
(
    ag_kit_id_ raw, 
    barcode_ varchar2
)
as
begin

  insert    into ag_kit_barcodes
            (ag_kit_id, barcode, sample_barcode_file)
  values    (ag_kit_id_, barcode_, barcode_ || '.jpg');
  
  commit;

end;