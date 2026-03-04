from flask import Flask, request, render_template, send_file
import pyodbc
import pandas as pd
import io
from datetime import datetime
import os

app = Flask(__name__)

DB_PATH = r"C:\ICOM\Database\CBOData_s.mdb"
CONN_STR = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={DB_PATH};"
    r"PWD=C0mtrex;"
)

def get_sales_day_number(target_date):
    queryDate = target_date.strftime('%m/%d/%Y')
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT SalesDayNumber FROM TransactionHeader WHERE Format(DateTimeStart, 'mm/dd/yyyy') = '{queryDate}'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def generate_excel_report(start_date_str, end_date_str):
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except:
        return None, "Invalid date format."
    
    conn = pyodbc.connect(CONN_STR)
    
    # Get all the SalesDayNumbers in the range
    query_days = f"SELECT DISTINCT SalesDayNumber, Format(DateTimeStart, 'mm/dd/yyyy') AS d FROM TransactionHeader WHERE DateTimeStart >= #{start_date.strftime('%m/%d/%Y')} 00:00:00# AND DateTimeStart <= #{end_date.strftime('%m/%d/%Y')} 23:59:59#"
    day_df = pd.read_sql(query_days, conn)
    
    if day_df.empty:
        conn.close()
        return None, "No data for this date range."
    
    days = day_df['SalesDayNumber'].tolist()
    days_str = ",".join([str(d) for d in days])
    
    # --- 1. HOURLY SALES ---
    hr_query = f"""
    SELECT 
        SlotNumber,
        SUM(GrossSalesin15Min) as GrossSales,
        SUM(NetSalesin15Min) as NetSales,
        SUM(GrossSalesin15Min) - SUM(NetSalesin15Min) as Discounts,
        SUM(CustCountin15Min) as Customers,
        SUM(TranCountin15Min) as Transactions
    FROM HourlySalesNew
    WHERE SalesDayNumber IN ({days_str})
    GROUP BY SlotNumber
    ORDER BY SlotNumber
    """
    hr_df = pd.read_sql(hr_query, conn)
    
    def format_slot(slot):
        mins = (slot * 15) - 15
        h = mins // 60; m = mins % 60
        e_mins = mins + 14
        e_h = e_mins // 60; e_m = e_mins % 60
        return f"{h:02d}:{m:02d} - {e_h:02d}:{e_m:02d}"
    
    if not hr_df.empty:
        hr_df['Time Period'] = hr_df['SlotNumber'].apply(format_slot)
        hr_df = hr_df[['Time Period', 'GrossSales', 'NetSales', 'Discounts', 'Customers', 'Transactions']]
    
    # --- 2. FINANCIAL SUMMARY ---
    fin_query = f"""
    SELECT 
        SUM(GrossSalesin15Min) as TotalGross,
        SUM(NetSalesin15Min) as TotalNet,
        SUM(CustCountin15Min) as TotalCustomers,
        SUM(TranCountin15Min) as TotalTransactions
    FROM HourlySalesNew
    WHERE SalesDayNumber IN ({days_str})
    """
    fin_df = pd.read_sql(fin_query, conn)
    
    # Get high-level totals from DailyCashierMisc
    misc_fin_query = f"""
    SELECT MiscDescription, SUM(MiscAmount) as TotalVal
    FROM DailyCashierMisc
    WHERE SalesDayNumber IN ({days_str}) AND MiscDescription IN ('Net Sales', 'Grand Control Total')
    GROUP BY MiscDescription
    """
    try:
        misc_fin_df = pd.read_sql(misc_fin_query, conn)
        for _, row in misc_fin_df.iterrows():
            if row['MiscDescription'] == 'Net Sales':
                fin_df['TotalNet'] = row['TotalVal']
            elif row['MiscDescription'] == 'Grand Control Total':
                fin_df['ChangeInGCTotal'] = row['TotalVal']
    except:
        pass
    
    # --- 3. SALES BY CATEGORY ---
    cat_query = f"""
    SELECT 
        C.CategoryName,
        SUM(D.MenuItemQuantity) as [Total Qty],
        SUM(D.MenuItemAmount) as [Total GrossSales],
        SUM(D.MenuItemAmount - D.MenuItemDiscAmount) as [Total NetSales]
    FROM DailyCashierSales D
    INNER JOIN (SELECT DISTINCT CategoryNumber, CategoryName FROM K_CategoryDefinitions) C ON D.CategoryNumber = C.CategoryNumber
    WHERE D.SalesDayNumber IN ({days_str})
    GROUP BY C.CategoryName
    """
    cat_df = pd.read_sql(cat_query, conn)
    
    cat_waiter_query = f"""
    SELECT 
        C.CategoryName,
        D.CashierName,
        SUM(D.MenuItemQuantity) as WaiterQty,
        SUM(D.MenuItemAmount - D.MenuItemDiscAmount) as WaiterNetSales
    FROM DailyCashierSales D
    INNER JOIN (SELECT DISTINCT CategoryNumber, CategoryName FROM K_CategoryDefinitions) C ON D.CategoryNumber = C.CategoryNumber
    WHERE D.SalesDayNumber IN ({days_str})
    GROUP BY C.CategoryName, D.CashierName
    """
    cat_waiter_df = pd.read_sql(cat_waiter_query, conn)
    
    if not cat_waiter_df.empty and not cat_df.empty:
        pivot_df = cat_waiter_df.pivot_table(index='CategoryName', columns='CashierName', values=['WaiterNetSales', 'WaiterQty'], aggfunc='sum', fill_value=0)
        pivot_df = pivot_df.swaplevel(axis=1).sort_index(axis=1)
        pivot_df.columns = [f"{c[0]}[$]" if c[1] == 'WaiterNetSales' else f"{c[0]}[Count]" for c in pivot_df.columns]
        pivot_df.reset_index(inplace=True)
        cat_df = pd.merge(pivot_df, cat_df, on='CategoryName', how='right')
        cat_df = cat_df.fillna(0)
        waiter_cols = [c for c in pivot_df.columns if c != 'CategoryName']
        cat_df = cat_df[['CategoryName'] + waiter_cols + ['Total Qty', 'Total GrossSales', 'Total NetSales']]
        
    cat_df = cat_df.sort_values(by='CategoryName')
    
    # --- 4. MEDIA & PAYMENTS (PIVOT BY WAITER) ---
    media_query = f"""
    SELECT 
        MediaName as ItemName,
        CashierName,
        SUM(POSQuantity) as Count_Tx,
        SUM(POSAmount) as ItemAmount
    FROM DailyCashierMedia
    WHERE SalesDayNumber IN ({days_str})
    GROUP BY MediaName, CashierName
    HAVING SUM(POSQuantity) > 0 OR SUM(POSAmount) <> 0
    """
    media_waiter_df = pd.read_sql(media_query, conn)
    
    misc_query = f"""
    SELECT 
        MiscDescription as ItemName,
        CashierName,
        SUM(MiscQuantity) as Count_Tx,
        SUM(MiscAmount) as ItemAmount
    FROM DailyCashierMisc
    WHERE SalesDayNumber IN ({days_str}) AND MiscDescription IN ('Error Corrects', 'MGR Void', 'Employee Disc', 'MGR Disc')
    GROUP BY MiscDescription, CashierName
    HAVING SUM(MiscQuantity) > 0 OR SUM(MiscAmount) <> 0
    """
    try:
        misc_waiter_df = pd.read_sql(misc_query, conn)
        media_waiter_df = pd.concat([media_waiter_df, misc_waiter_df], ignore_index=True)
    except:
        pass
        
    media_df = pd.DataFrame()
    if not media_waiter_df.empty:
        # Get total row per MediaItem across all waiters:
        media_totals = media_waiter_df.groupby('ItemName')[['Count_Tx', 'ItemAmount']].sum().reset_index()
        media_totals.rename(columns={'Count_Tx': 'Total Count', 'ItemAmount': 'Total Amount'}, inplace=True)
        
        # Pivot amount AND count by waiter
        pivot_media = media_waiter_df.pivot_table(index='ItemName', columns='CashierName', values=['ItemAmount', 'Count_Tx'], aggfunc='sum', fill_value=0)
        pivot_media = pivot_media.swaplevel(axis=1).sort_index(axis=1)
        pivot_media.columns = [f"{c[0]}[$]" if c[1] == 'ItemAmount' else f"{c[0]}[Count]" for c in pivot_media.columns]
        pivot_media.reset_index(inplace=True)
        
        # Merge totals to the right
        media_df = pd.merge(pivot_media, media_totals, on='ItemName', how='left')
        media_df = media_df.fillna(0)
        
        media_waiter_cols = [c for c in pivot_media.columns if c != 'ItemName']
        # Reorder so totals are at the end
        media_df = media_df[['ItemName'] + media_waiter_cols + ['Total Count', 'Total Amount']]
        media_df = media_df.sort_values(by='ItemName')
    
    # --- 5. SERVER / WAITER REPORT ---
    waiter_query = f"""
    SELECT 
        CashierName,
        SUM(MenuItemQuantity) as ItemsSold,
        SUM(MenuItemAmount) as GrossSales,
        SUM(MenuItemDiscAmount) as Discounts,
        SUM(MenuItemAmount - MenuItemDiscAmount) as NetSales
    FROM DailyCashierSales
    WHERE SalesDayNumber IN ({days_str})
    GROUP BY CashierName
    ORDER BY CashierName
    """
    waiter_df = pd.read_sql(waiter_query, conn)
    
    # --- 6. PRODUCT SALES / PLATOS VENDIDOS ---
    prod_query = f"""
    SELECT 
        ProductName,
        CashierName,
        SUM(MenuItemQuantity) as WaiterQty,
        SUM(MenuItemAmount - MenuItemDiscAmount) as WaiterNetSales
    FROM DailyCashierSales
    WHERE SalesDayNumber IN ({days_str})
    GROUP BY ProductName, CashierName
    """
    prod_waiter_df = pd.read_sql(prod_query, conn)
    
    prod_df = pd.DataFrame()
    if not prod_waiter_df.empty:
        prod_totals = prod_waiter_df.groupby('ProductName')[['WaiterQty', 'WaiterNetSales']].sum().reset_index()
        prod_totals.rename(columns={'WaiterQty': 'Total Qty', 'WaiterNetSales': 'Total NetSales'}, inplace=True)
        
        pivot_prod = prod_waiter_df.pivot_table(index='ProductName', columns='CashierName', values=['WaiterNetSales', 'WaiterQty'], aggfunc='sum', fill_value=0)
        pivot_prod = pivot_prod.swaplevel(axis=1).sort_index(axis=1)
        pivot_prod.columns = [f"{c[0]}[$]" if c[1] == 'WaiterNetSales' else f"{c[0]}[Count]" for c in pivot_prod.columns]
        pivot_prod.reset_index(inplace=True)
        
        prod_df = pd.merge(pivot_prod, prod_totals, on='ProductName', how='left')
        prod_df = prod_df.fillna(0)
        waiter_prod_cols = [c for c in pivot_prod.columns if c != 'ProductName']
        prod_df = prod_df[['ProductName'] + waiter_prod_cols + ['Total Qty', 'Total NetSales']]
        prod_df = prod_df.sort_values(by='ProductName')

    conn.close()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        fin_df.to_excel(writer, sheet_name='Financial Summary', index=False)
        cat_df.to_excel(writer, sheet_name='Category Sales', index=False)
        media_df.to_excel(writer, sheet_name='Media & Adjustments', index=False)
        waiter_df.to_excel(writer, sheet_name='Server Report', index=False)
        if not prod_df.empty:
            prod_df.to_excel(writer, sheet_name='Product Sales', index=False)
        
        # Add hourly sales
        if not hr_df.empty:
            hr_df.to_excel(writer, sheet_name='Hourly Sales', index=False)
            
    output.seek(0)
    return output, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if not end_date:
            end_date = start_date
            
        file_obj, err = generate_excel_report(start_date, end_date)
        if err:
            return render_template('index.html', error=err)
            
        return send_file(
            file_obj, 
            as_attachment=True, 
            download_name=f"Report_{start_date}_to_{end_date}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
