(* 占位：这里放被测程序 final.st。
   成员2 只需要保证这个文件 + test/actual/*.csv 存在。 *)
FUNCTION_BLOCK FB_AlarmHandling
VAR_INPUT
    Value : REAL;
    hiLevel : REAL;
    loLevel : REAL;
    hystWindow : REAL;
END_VAR
VAR_OUTPUT
    hiAlarm : BOOL;
    loAlarm : BOOL;
    error : BOOL;
    status : WORD;
END_VAR
(* 实现由成员2 生成 *)
END_FUNCTION_BLOCK
