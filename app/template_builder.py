from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import date, timedelta

def build_template(path):
    wb=Workbook(); wb.remove(wb.active)
    sheets={
      "PROJECTS":["Project_ID","Customer","Sales","PM","Order_Value","Status","Technical_Status","Country"],
      "MILESTONES":["Project_ID","Milestone","Contract_Date","Forecast_Date","Actual_Date","Invoice_Value","Invoice_Required","LD_Applicable","LD_Rate_Weekly_Pct"],
      "BUDGET":["Project_ID","Category","Budget","Actual","Committed","ETC","ETC_Source"],
      "COSTS":["Project_ID","Category","Cost_Date","Amount","Description"],
      "INVOICES":["Project_ID","Invoice_Number","Milestone","Issue_Date","Due_Date","Amount","Paid_Amount"],
      "PAYMENTS":["Project_ID","Invoice_Number","Payment_Date","Amount"],
      "ACTIONS":["Project_ID","Title","Owner","Due_Date","Status"],
      "COMMUNICATIONS":["Project_ID","Date","Direction","Sender","Recipient","Subject","Body","Topic","Responded","Reminders_Count","Source_Ref"],
      "CUSTOMER_ORDERS":["Project_ID","Order_Number","Order_Date","Order_Kind","Quote_Ref","Net_Value","Tax_Value","Gross_Value","Currency","Payment_Terms","Incoterm","Scope_Summary","Source_Ref","Note"],
      "CHANGES":["Project_ID","Description","Date","Estimated_Cost","Quoted_Value","Order_Received","Work_Started","Source_Ref"],
      "CONTROL_SNAPSHOT":["Project_ID","Snapshot_Date","Source_Label","Baseline_Budget","Operational_Budget","Orders_JMRP","Orders_Extract","Received","Open_Order_Commitment","Labor","Overhead","Note"],
      "CONTROL_LINES":["Project_ID","Snapshot_Date","VDA_Code","VDA_Name","Analysis_Center","Baseline_Budget","Operational_Budget","Ordered","Received","Open_Order_Commitment","Labor","Overhead","Purchases_Closed","Source_Ref"],
    }
    today=date.today()
    examples={
      "PROJECTS":["P-EX001","Example Industries","S. Riva","A. Greco",750000,"EXECUTION","IN_PROGRESS","IT"],
      "MILESTONES":["P-EX001","Delivery",today+timedelta(days=30),today+timedelta(days=35),None,150000,True,True,0.5],
      "BUDGET":["P-EX001","Mechanical",320000,180000,90000,60000,"MANUAL"],
      "COSTS":["P-EX001","Mechanical",today-timedelta(days=10),25000,"Example cost"],
      "INVOICES":["P-EX001","INV-001","Down payment",today-timedelta(days=60),today-timedelta(days=30),150000,150000],
      "PAYMENTS":["P-EX001","INV-001",today-timedelta(days=25),150000],
      "ACTIONS":["P-EX001","Confirm FAT date","A. Greco",today+timedelta(days=7),"OPEN"],
      "COMMUNICATIONS":["P-EX001",today,"INBOUND","client@example.com","pm@brofind.example","FAT schedule","Unfortunately the FAT will be postponed by two weeks. Please confirm the revised date.","FAT","FALSE",0,"excel:mail-001"],
      "CUSTOMER_ORDERS":["P-EX001","PO-001",today,"BASE","OFF-001",750000,0,750000,"EUR","60 giorni data fattura","DDP","Impianto base","contract:PO-001","Esempio"],
      "CHANGES":["P-EX001","Extra ventilatore",today,25000,40000,"TRUE","TRUE","contract:PO-EXTRA-001"],
      "CONTROL_SNAPSHOT":["P-EX001",today,"Galileo · demo",500000,520000,315000,314900,180000,134900,12000,3000,"Forecast finale non stimato"],
      "CONTROL_LINES":["P-EX001",today,"C000013","CARPENTERIE METALLICHE","COMM",180000,190000,165000,90000,75000,0,0,"S","galileo:demo:C000013"],
    }
    for name, headers in sheets.items():
        ws=wb.create_sheet(name)
        ws.append(headers); ws.append(examples[name])
        for c in ws[1]:
            c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill("solid", fgColor="1F4E78"); c.alignment=Alignment(horizontal="center")
        for col in range(1,len(headers)+1): ws.column_dimensions[get_column_letter(col)].width=max(14,min(28,len(headers[col-1])+4))
        ws.freeze_panes="A2"
    wb.save(path)
