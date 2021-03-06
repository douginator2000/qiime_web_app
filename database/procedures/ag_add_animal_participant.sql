create or replace
procedure ag_add_animal_participant
(
    ag_login_id_ raw,
    participant_name_ varchar2
)
as
begin

    merge into ag_animal_survey
    using dual
    on 
    (
        dual.dummy is not null
        and ag_animal_survey.ag_login_id = ag_login_id_
        and ag_animal_survey.participant_name = participant_name_
    )
    when not matched then 
        insert (ag_login_id, participant_name) 
        values (ag_login_id_, participant_name_);

    commit;
end;
