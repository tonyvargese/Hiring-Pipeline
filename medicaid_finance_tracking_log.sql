SELECT DISTINCT *
FROM (
   
    SELECT DISTINCT
       p.*,
       NULL AS vendor_no,
       MIN(p.labeler_cd) OVER (
           PARTITION BY p.stlmnt_num, p.mQuarter
       ) AS mlabeler_cd
 FROM (
    SELECT DISTINCT
           latest_rows.stlmnt_num,
           latest_rows.stlmntmthd_num,
           latest_rows.cont_num,
           latest_rows.stlmnt_bunit_num,
           latest_rows.status_desc,
           latest_rows.check_requested_date,
           latest_rows.bunit_id_pri,
           latest_rows.bunit_name,
           --nvl(d.cont_internal_id,g.cont_internal_id) as cont_internal_id,
           LISTAGG(
               DISTINCT latest_rows.raw_program,
               ', '
           ) WITHIN GROUP (
               ORDER BY latest_rows.raw_program
           ) OVER (
               PARTITION BY
                   latest_rows.stlmnt_num,
                   latest_rows.stlmntmthd_num,
                   latest_rows.mQuarter
           ) AS cont_internal_id,
           latest_rows.Quarter,
           latest_rows.mQuarter,
           latest_rows.labeler_cd,
           latest_rows.userid,
           latest_rows.MailDt_Notes,
           latest_rows.Void_Notes,
           latest_rows.Workflow_Notes,
           latest_rows.username,
           latest_rows.check_amt,
           latest_rows."Date Required",
           latest_rows."Date Sent To Accounting",
           latest_rows."Date Paid",
           latest_rows."Date Processed by Accounting",
           latest_rows."Accounting Date",
           latest_rows."Check or EFT",
           latest_rows."Check#",
           latest_rows.mds_num
    FROM (
        SELECT base_rows.*
        FROM (SELECT
      e.stlmnt_num,
      f.stlmntmthd_num,
  e.cont_num ,
--a.cont_num as cont_num_req,
--NVL(d.cont_internal_id, g.cont_internal_id) AS raw_cont_internal_id,
--a.cont_num AS raw_cont_num_req,
--LISTAGG(
--    DISTINCT a.cont_num,
--    ', '
--) WITHIN GROUP (
--    ORDER BY a.cont_num
--) OVER (
--    PARTITION BY e.stlmnt_num
--) AS cont_num_req,
     e.stlmnt_bunit_num,
(SELECT  status_desc FROM status b where status_cd = 'stlmntmeth' and b.status_num = f.stlmntmthd_status_num ) as status_desc,
      SYSDATE    check_requested_date,
      c.bunit_id_pri,
      c.bunit_name,
            --nvl(d.cont_internal_id,g.cont_internal_id) as cont_internal_id,
            NVL(d.cont_internal_id, g.cont_internal_id) AS raw_program,


   TO_CHAR(b.adj_dt_start,'YYYYQ') Quarter,
  max(TO_CHAR(b.adj_dt_start,'YYYYQ')) OVER (PARTITION BY a.stlmnt_num) mQuarter,
      b.labeler_cd,
      e.userid,
          (select note_txt from (select note_txt, RANK () over (order by note_dt_enter desc) as rank_num from NOTE 
where  note_tablename = 'STLMNT' and note_rownum=e.stlmnt_num and  notetyp_id = 'MAIL DATE' ) where rank_num=1) MailDt_Notes,
    (select note_txt from (select note_txt, RANK () over (order by note_dt_enter desc) as rank_num from NOTE 
where  note_tablename = 'STLMNT' and note_rownum=e.stlmnt_num and  notetyp_id = 'VOID RESON' ) where rank_num=1) Void_Notes,
    (select note_txt from (select note_txt, RANK () over (order by note_dt_enter desc) as rank_num from NOTE 
where  note_tablename = 'STLMNT' and note_rownum=e.stlmnt_num and  notetyp_id = 'WORKFLOWID' ) where rank_num=1) Workflow_Notes,
      (select txt_opr_nme_lst from topr where  num_opR_id = e.userid) as username,
   e.stlmnt_amount check_amt,
       f.stlmntmthd_dt_required "Date Required" ,
f.stlmntmthd_dt_requested        as "Date Sent To Accounting",
       f.stlmntmthd_dt_sent as "Date Paid",
f.stlmntmthd_dt_acct as "Date Processed by Accounting",
f.stlmntmthd_dt_docno as "Accounting Date",

        f.stltyp_cd as "Check or EFT",
        f.stlmntmthd_docno as "Check#",
    --  imany_utility_pkg.get_vendor_no(b.adj_cont_num, b.labeler_cd, b.adj_bunit_num, a.stlmnt_num) vendor_no,


      b.mds_num
   FROM
      adjreq a, adj b, bunit c, cont d, stlmnt e,stlmntmthd f,cont g
	  -- (select M.MDS_NUM,
       -- M.MDS_ORG_ID      as DIVISION_UNIQUE_NAME,
       -- M.MDS_NAME          as DIVISION_NAME,
       -- M.CURRENCY_CD,
       -- substr(T.TXT_OPR_ID, 1, INSTR(T.TXT_OPR_ID, '@', 1, 1) - 1) as user_name,
       -- T.NUM_OPR_ID      as USER_ID
  -- from MDS M, MDSUSER U, TOPR T
 -- where M.MDS_NUM = U.MDS_NUM
   -- and U.NUM_OPR_ID = T.NUM_OPR_ID
-- and substr(T.TXT_OPR_ID, 1, INSTR(T.TXT_OPR_ID, '@', 1, 1) - 1) = #sq($account.personalInfo.userName)#  ) ds
   WHERE
   b.adjtyp_cd  = 'MEDI'          
       and a.adj_type = 'MEDI'
      and e.apptyp_id = 'MEDI'
--AND trunc(f.stlmntmthd_dt_requested) between TO_DATE('2026-05-10', 'YYYY-MM-DD') and  TO_DATE('2026-07-10','YYYY-MM-DD')
  --and e.cont_num in (56434006,55022341) 
  -- or -1 in (#promptmany('Prog', 'integer',-1) #))
-- and (f.stlmntmthd_status_num in (#promptmany('status', 'integer',-1) #) or -1 in (#promptmany('status', 'integer',-1) #))
and      b.adj_num    = a.adj_num       AND
         -- (ds.mds_num = b.mds_num) and 
      c.bunit_num  = e.stlmnt_bunit_num AND
             e.cont_num = d.cont_num(+)    AND
a.cont_num = g.cont_num(+) and 
      e.stlmnt_num = a.stlmnt_num and
      e.stlmnt_num = f.stlmnt_num   
and e.stlmnt_num = 56406520
--in(55750246,
--55759313,
--55878029,
--55752167) 
    ) base_rows
        WHERE base_rows.quarter = base_rows.mQuarter
    ) latest_rows
 ) p
union all
 SELECT DISTINCT
       p.*,
       NULL AS vendor_no,
       MIN(p.labeler_cd) OVER (
           PARTITION BY p.stlmnt_num, p.mQuarter
       ) AS mlabeler_cd
 FROM (
    SELECT DISTINCT
           latest_rows.stlmnt_num,
           latest_rows.stlmntmthd_num,
           latest_rows.cont_num,
           latest_rows.stlmnt_bunit_num,
           latest_rows.status_desc,
           latest_rows.check_requested_date,
           latest_rows.bunit_id_pri,
           latest_rows.bunit_name,
           --nvl(d.cont_internal_id,g.cont_internal_id) as cont_internal_id,
           LISTAGG(
               DISTINCT latest_rows.raw_program,
               ', '
           ) WITHIN GROUP (
               ORDER BY latest_rows.raw_program
           ) OVER (
               PARTITION BY
                   latest_rows.stlmnt_num,
                   latest_rows.stlmntmthd_num,
                   latest_rows.mQuarter
           ) AS cont_internal_id,
           latest_rows.Quarter,
           latest_rows.mQuarter,
           latest_rows.labeler_cd,
           latest_rows.userid,
           latest_rows.MailDt_Notes,
           latest_rows.Void_Notes,
           latest_rows.Workflow_Notes,
           latest_rows.username,
           latest_rows.check_amt,
           latest_rows."Date Required",
           latest_rows."Date Sent To Accounting",
           latest_rows."Date Paid",
           latest_rows."Date Processed by Accounting",
           latest_rows."Accounting Date",
           latest_rows."Check or EFT",
           latest_rows."Check#",
           latest_rows.mds_num
    FROM (
        SELECT base_rows.*
        FROM (SELECT
      e.stlmnt_num,
      f.stlmntmthd_num,
  e.cont_num ,
--a.cont_num as cont_num_req,
--NVL(d.cont_internal_id, g.cont_internal_id) AS raw_cont_internal_id,
--a.cont_num AS raw_cont_num_req,
--LISTAGG(
--    DISTINCT a.cont_num,
--    ', '
--) WITHIN GROUP (
--    ORDER BY a.cont_num
--) OVER (
--    PARTITION BY e.stlmnt_num
--) AS cont_num_req,
     e.stlmnt_bunit_num,
(SELECT  status_desc FROM status b where status_cd = 'stlmntmeth' and b.status_num = f.stlmntmthd_status_num ) as status_desc,
      SYSDATE    check_requested_date,
      c.bunit_id_pri,
      c.bunit_name,
           --nvl(d.cont_internal_id,g.cont_internal_id) as cont_internal_id,
           NVL(d.cont_internal_id, g.cont_internal_id) AS raw_program,

   TO_CHAR(b.adj_dt_start,'YYYYQ') Quarter,
  max(TO_CHAR(b.adj_dt_start,'YYYYQ')) OVER (PARTITION BY a.stlmnt_num) mQuarter,
      b.labeler_cd,
      e.userid,
          (select note_txt from (select note_txt, RANK () over (order by note_dt_enter desc) as rank_num from NOTE 
where  note_tablename = 'STLMNT' and note_rownum=e.stlmnt_num and  notetyp_id = 'MAIL DATE' ) where rank_num=1) MailDt_Notes,
    (select note_txt from (select note_txt, RANK () over (order by note_dt_enter desc) as rank_num from NOTE 
where  note_tablename = 'STLMNT' and note_rownum=e.stlmnt_num and  notetyp_id = 'VOID RESON' ) where rank_num=1) Void_Notes,
    (select note_txt from (select note_txt, RANK () over (order by note_dt_enter desc) as rank_num from NOTE 
where  note_tablename = 'STLMNT' and note_rownum=e.stlmnt_num and  notetyp_id = 'WORKFLOWID' ) where rank_num=1) Workflow_Notes,
      (select txt_opr_nme_lst from topr where  num_opR_id = e.userid) as username,
   e.stlmnt_amount check_amt,
       f.stlmntmthd_dt_required "Date Required" ,
f.stlmntmthd_dt_requested        as "Date Sent To Accounting",
       f.stlmntmthd_dt_sent as "Date Paid",
f.stlmntmthd_dt_acct as "Date Processed by Accounting",
f.stlmntmthd_dt_docno as "Accounting Date",

        f.stltyp_cd as "Check or EFT",
        f.stlmntmthd_docno as "Check#",
    --  imany_utility_pkg.get_vendor_no(b.adj_cont_num, b.labeler_cd, b.adj_bunit_num, a.stlmnt_num) vendor_no,


      b.mds_num
   FROM
      adjreq a, adj b, bunit c, cont d, stlmnt e,stlmntmthd f,cont g
-- (select M.MDS_NUM,
       -- M.MDS_ORG_ID      as DIVISION_UNIQUE_NAME,
       -- M.MDS_NAME          as DIVISION_NAME,
       -- M.CURRENCY_CD,
       -- substr(T.TXT_OPR_ID, 1, INSTR(T.TXT_OPR_ID, '@', 1, 1) - 1) as user_name,
       -- T.NUM_OPR_ID      as USER_ID
  -- from MDS M, MDSUSER U, TOPR T
 -- where M.MDS_NUM = U.MDS_NUM
   -- and U.NUM_OPR_ID = T.NUM_OPR_ID
-- and substr(T.TXT_OPR_ID, 1, INSTR(T.TXT_OPR_ID, '@', 1, 1) - 1) = #sq($account.personalInfo.userName)#  ) ds
   WHERE
   b.adjtyp_cd  = 'MEDI'          
       and a.adj_type = 'MEDI'
      and e.apptyp_id = 'MEDI'
-- and #prompt('IBD','integer',0)# =1
and f.stlmntmthd_dt_requested is null
  --and e.cont_num in (56434006,55022341)
  -- or -1 in (#promptmany('Prog', 'integer',-1) #))
-- and (f.stlmntmthd_status_num in (#promptmany('status', 'integer',-1) #) or -1 in (#promptmany('status', 'integer',-1) #))
and      b.adj_num    = a.adj_num       AND
      -- (ds.mds_num = b.mds_num) and 
      c.bunit_num  = e.stlmnt_bunit_num AND
       e.cont_num = d.cont_num(+)    AND
a.cont_num = g.cont_num(+) and 
      e.stlmnt_num = a.stlmnt_num and
      e.stlmnt_num = f.stlmnt_num   
and e.stlmnt_num =56179929
    ) base_rows
        WHERE base_rows.quarter = base_rows.mQuarter
    ) latest_rows
 ) p
);
