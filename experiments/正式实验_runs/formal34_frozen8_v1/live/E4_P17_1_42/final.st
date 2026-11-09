TYPE ST_Recipe :
STRUCT
    recipeID : INT;
    ingredientType : INT;
    ingredientRatio : REAL;
    productionTemperature : REAL;
END_STRUCT
END_TYPE

FUNCTION_BLOCK FB_P17
VAR_INPUT
    addRecipe : BOOL;
    deleteRecipe : BOOL;
    modifyRecipe : BOOL;
    queryRecipe : BOOL;
    recipeIn : ST_Recipe;
    recipeID : INT;
    ingredientType : INT;
    ingredientRatio : REAL;
    productionTemperature : REAL;
END_VAR
VAR_OUTPUT
    recipeAdded : BOOL := FALSE;
    recipeDeleted : BOOL := FALSE;
    recipeModified : BOOL := FALSE;
    recipeQueryResult : ST_Recipe;
    error : BOOL := FALSE;
    status : WORD := WORD#16#0000;
END_VAR
VAR_IN_OUT
    recipe : ARRAY[1..10] OF ST_Recipe;
END_VAR
VAR
    initialized : BOOL := FALSE;
    previousAdd : BOOL := FALSE;
    previousDelete : BOOL := FALSE;
    previousModify : BOOL := FALSE;
    previousQuery : BOOL := FALSE;
    addEdge : BOOL;
    deleteEdge : BOOL;
    modifyEdge : BOOL;
    queryEdge : BOOL;
    i : INT;
    foundIndex : INT;
    emptyIndex : INT;
    operation : INT;
END_VAR

(*
    每次调用代表一个20 ms扫描；请求采用上升沿，成功标志为单扫描脉冲。
    错误及状态码保持到下一个被处理的请求。

    待审事项：
    1. I/O表比骨架多四个标量输入；全部保留接口。
       按需求原文使用recipeIn字段，标量输入不替代结构字段。
    2. K1“写入只能落到空位”与原文“修改替换已有配方”冲突。
       此实现按原文执行原位修改；K1的空位限制用于新增。
    3. 同时请求的仲裁未规定。本实现一次仅处理一个上升沿，
       优先级为删除、修改、新增、查询；其他同时上升沿不排队。
    4. 编号0为空位，不作为可查询、删除或修改的配方。
       新增0按原文比较规则：有空位报重复，无空位报满库。
       原题未提供独立的无效编号错误码。
    5. C10要求首扫描无错误、无成功，首扫描不执行请求。
       首扫描仍为高的请求在第二扫描作为首次上升沿处理；
       仅在首扫描出现的请求不执行，启动请求行为待审。
    6. IN_OUT数据库的全空初态由调用方提供；不擅自清空外部数据。
       本源码未声称经过编译或逐周期功能验证。
*)

recipeAdded := FALSE;
recipeDeleted := FALSE;
recipeModified := FALSE;

IF NOT initialized THEN
    error := FALSE;
    status := WORD#16#0000;
    recipeQueryResult.recipeID := 0;
    recipeQueryResult.ingredientType := 0;
    recipeQueryResult.ingredientRatio := REAL#0.0;
    recipeQueryResult.productionTemperature := REAL#0.0;

    previousAdd := FALSE;
    previousDelete := FALSE;
    previousModify := FALSE;
    previousQuery := FALSE;
    initialized := TRUE;
ELSE
    addEdge := addRecipe AND NOT previousAdd;
    deleteEdge := deleteRecipe AND NOT previousDelete;
    modifyEdge := modifyRecipe AND NOT previousModify;
    queryEdge := queryRecipe AND NOT previousQuery;

    previousAdd := addRecipe;
    previousDelete := deleteRecipe;
    previousModify := modifyRecipe;
    previousQuery := queryRecipe;

    operation := 0;
    IF deleteEdge THEN
        operation := 1;
    ELSIF modifyEdge THEN
        operation := 2;
    ELSIF addEdge THEN
        operation := 3;
    ELSIF queryEdge THEN
        operation := 4;
    END_IF;

    IF operation <> 0 THEN
        error := FALSE;
        status := WORD#16#0000;
        foundIndex := 0;
        emptyIndex := 0;

        FOR i := 1 TO 10 DO
            IF (recipe[i].recipeID = 0) AND (emptyIndex = 0) THEN
                emptyIndex := i;
            END_IF;

            IF (recipeIn.recipeID <> 0)
                AND (recipe[i].recipeID = recipeIn.recipeID)
                AND (foundIndex = 0) THEN
                foundIndex := i;
            END_IF;
        END_FOR;

        CASE operation OF
            1:
                IF foundIndex = 0 THEN
                    error := TRUE;
                    status := WORD#16#8004;
                ELSE
                    recipe[foundIndex].recipeID := 0;
                    recipeDeleted := TRUE;
                END_IF;

            2:
                IF foundIndex = 0 THEN
                    error := TRUE;
                    status := WORD#16#8005;
                ELSE
                    recipe[foundIndex] := recipeIn;
                    recipeModified := TRUE;
                END_IF;

            3:
                IF (foundIndex <> 0)
                    OR ((recipeIn.recipeID = 0) AND (emptyIndex <> 0)) THEN
                    error := TRUE;
                    status := WORD#16#8002;
                ELSIF emptyIndex = 0 THEN
                    error := TRUE;
                    status := WORD#16#8003;
                ELSE
                    recipe[emptyIndex] := recipeIn;
                    recipeAdded := TRUE;
                END_IF;

            4:
                IF foundIndex = 0 THEN
                    error := TRUE;
                    status := WORD#16#8001;
                ELSE
                    recipeQueryResult := recipe[foundIndex];
                END_IF;
        END_CASE;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
