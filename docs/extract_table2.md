
1. Extract table data from given pdf file.
2. Only extract Table 2 , Table 2aa , Table 2a , Table 2b , Table 3a data.
3. Table 2 data range: 
    Start page: 56
    End Page: 76
    Table Cols: 8
    First Row (col 1): 1111 Chief
    Last Row (col 1): 3556 Sales

4. Table 2aa data range:
    Start page: 77
    End Page: 112
    Table Cols: 8
    First Row (col 1): 1150 Managers
    Last Row (col 1): 9249 Elementary

5. Table 2a data range:
    Start page: 113
    End Page: 114
    Table Cols: 6
    First Row (col 1): 3214
    Last Row (col 1): 9252

6. Table 2b data range:
    Start page: 115
    End Page: 118
    Table Cols: 6
    First Row (col 1): 1232
    Last Row (col 1): 3543 Project

7. Table 3a data range:
    Start page: 119
    End Page: 121
    Table Cols: 5
    First Row (col 1): 3213 Medical
    Last Row (col 1): 6133 Dental


8. data process:
    - Table2, col3: retain "\n" in data and can be output in Excel.
    - Table2, col4 to col7: split amount and rate data. Exmaple: £88,100 (£45.18 per hour) to £88,100 and £45.18

6. the output data for Table 2 should have 12 cols. because original col4 to col7 will split in to 2 cols.
7. Store each table data in sheet with their name, such as "Table 1"