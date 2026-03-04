import pandas as pd
df = pd.DataFrame({
    'CategoryName': ['Appetizers', 'Appetizers', 'Drinks', 'Drinks'],
    'CashierName': ['Laura', 'Juan', 'Laura', 'Juan'],
    'WaiterQty': [2, 3, 5, 1],
    'WaiterNetSales': [20.0, 30.0, 10.0, 2.0]
})

pivot_df = df.pivot_table(index='CategoryName', columns='CashierName', values=['WaiterNetSales', 'WaiterQty'], aggfunc='sum', fill_value=0)
pivot_df = pivot_df.swaplevel(axis=1).sort_index(axis=1)

pivot_df.columns = [f"{c[0]}[$]" if c[1] == 'WaiterNetSales' else f"{c[0]}[Count]" for c in pivot_df.columns]
pivot_df.reset_index(inplace=True)

print(pivot_df)
