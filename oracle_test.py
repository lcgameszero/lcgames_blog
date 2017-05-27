import cx_Oracle
# ORCL为远端oracle配置的listener的名称
dsn_tns = cx_Oracle.makedsn('192.168.14.203', 1521,'ORCL')   
print cx_Oracle.connect('tax','tax',dsn_tns)