
1. Extract table data from given pdf file.
2. Only extract Table 1 and Table 1a data.
3. Table 1 data range: 
    Start page: 13
    End Page: 28
    Table Cols: 7
    First Row (col 1): 1111 Chief executives and senior officials
    Last Row (col 1): 3556 Sales accounts and business development managers

4. Table 1a data range:
    Start page: 29
    End Page: 55
    Table Cols: 7
    First Row (col 1): 1150 Managers and directors in retail and wholesale
    Last Row (col 1): 9249 Elementary sales occupations not elsewhere classified

5. data process:
    - col2: retain "\n" in data and can be output in Excel.
    - col3 to col6: split amount and rate data. Exmaple: £88,100 (£45.18 per hour) to £88,100 and £45.18

6. the output data should have 11 cols. because original col3 to col6 will split in to 2 cols.
7. Store Table 1 data in sheet with name "Table 1"
8. Store Table 1a data in sheet with name "Table 1a"