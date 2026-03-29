import mysql.connector, json
cfg=json.load(open('c:/ICOM/Database/config.json'))
conn=mysql.connector.connect(host=cfg['remote_db_host'], user=cfg['remote_db_user'], password=cfg['remote_db_pass'], database=cfg['remote_db_name'], use_pure=True)
c=conn.cursor()
metrics = {k: 0.0 for k in ['cash','employee_disc','error_corrects','gratuity',
                            'mgr_disc','mgr_void','sales_transfer_in','sales_transfer_out',
                            'service_balance','tax_1','tips_paid','net_sales','change_in_gc_total']}
try:
    c.execute("""INSERT INTO restaurantes_diario_media
        (restaurante, fecha, cash, employee_disc, error_corrects, gratuity, mgr_disc, mgr_void,
         sales_transfer_in, sales_transfer_out, service_balance, tax_1, tips_paid, net_sales, change_in_gc_total)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        ('Little Mexico Bowdon', '2026-03-28', metrics['cash'], metrics['employee_disc'],
         metrics['error_corrects'], metrics['gratuity'], metrics['mgr_disc'], metrics['mgr_void'],
         metrics['sales_transfer_in'], metrics['sales_transfer_out'], metrics['service_balance'],
         metrics['tax_1'], metrics['tips_paid'], metrics['net_sales'], metrics['change_in_gc_total']))
    conn.commit()
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
    
c.execute("SELECT COUNT(*) FROM restaurantes_diario_media WHERE restaurante='Little Mexico Bowdon' AND fecha='2026-03-28'")
print('DIARIO_MEDIA COUNT AFTER INSERT:', c.fetchone()[0])
