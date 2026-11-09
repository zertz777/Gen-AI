(*
修改说明：
保留原声明接口，以逐扫描逻辑实现配方管理。
每次调用代表 20 ms；无需定时器。
根据权威编译器错误，将 END_STRUCT 后的分号移除。
快速编译器此前要求该分号，而权威编译器拒绝该分号；
两个编译 profile 的类型声明语法要求存在冲突。
本版本采用此前权威编译通过的无分号形式，
不声称同时通过快速编译器和权威编译器。
recipe 为调用方管理的 IN_OUT 数据库，不在功能块中主动初始化。
从首次调用开始处理请求，保留调用方预置配方。
成功标志每扫描清零；error/status 保持到下一次处理请求。
输出初值通过声明设置，不增加初始化专用扫描。
此处无法访问本地编译器、已配置测试命令或执行环境；
未重新运行编译或逐周期测试，不声称已验证正确。

【必留：需求原文】
A factory's production line needs to produce a variety of products based on different recipes. The control center of the production line requires a recipe management system that allows operators to add, delete, modify, and query recipe data.
Control requirements:
Recipe data should include recipe number, raw material type, raw material ratio, and production temperature.
The system should allow input of new recipe data and store it in the recipe database.
The system should allow deletion or modification of existing recipe data by recipe number.
The system should allow querying recipe details by recipe number and output the recipe.
Notes:
1. Recipes are constructed using the ST_Recipe data type, which includes recipe number (recipeID), raw material type (ingredientType), raw material ratio (ingredientRatio), and production temperature (productionTemperature). The recipe database can store up to 10 recipes, constructed with ARRAY[1..10] OF ST_Recipe, where recipe numbers must not be duplicated, and a recipe number of 0 indicates an empty slot.
2. When a query recipe request signal (queryRecipe) is triggered, the system first compares the recipe number (recipeID) from the input recipe (recipeIn) with all recipes in the recipe database recipe. If the number does not exist, an error status (error=true) and error code (status=16#8001) are output. If the number exists, the recipe is output to the recipe query result (recipeQueryResult).
3. When an add recipe request signal (addRecipe) is triggered, the system first compares the recipe number (recipeID) from the input recipe (recipeIn) with all recipes in the recipe database (recipe). If a duplicate number exists, an error status (error=true) and error code (status=16#8002) are output. If there is no empty slot in the recipe database (recipe), an error status (error=true) and error code (status=16#8003) are output. If there are no errors, the input recipe (recipeIn) is stored in the recipe database (recipe), prioritizing the empty slot with the smallest array index.
4. When a delete recipe request signal (deleteRecipe) is triggered, the system first compares the recipe number (recipeID) from the input recipe (recipeIn) with all recipes in the recipe database (recipe). If the number does not exist, an error status (error=true) and error code (status=16#8004) are output. If the number exists, the recipe is deleted, i.e., the recipe number (recipeID) in the recipe database (recipe) is set to 0.
5. When a modify recipe request signal (modifyRecipe) is triggered, the system first compares the recipe number (recipeID) from the input recipe (recipeIn) with all recipes in the recipe database (recipe). If the number does not exist, an error status (error=true) and error code (status=16#8005) are output. If the number exists, the recipe is replaced with the input recipe (recipeIn).

中文摘要：配方管理：配方库最多 10 条（编号 0 表示空位），支持增删改查；
查询不存在报 16#8001，重复新增报 16#8002，满库报 16#8003，
删除不存在报 16#8004，修改不存在报 16#8005。
扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【接口、初态、约束与数据告警】
task_id: P17
title: Recipe Management System
接口名称、方向及类型保留为下方 TYPE 和 FUNCTION_BLOCK 声明。
需求初态：全部 recipeID = 0；error = FALSE；status = 16#0000；
recipeAdded、recipeDeleted、recipeModified = FALSE。
数据库初态由调用方提供，本功能块不清空 IN_OUT 数据库。
K1 配方库容量 10 条，recipeID = 0 表示空位；写入时只能落到空位。
K2 新增时若库中已存在相同 recipeID，拒绝写入并置 status = 16#8002。
K3 查询时若 recipeID 不存在，置 status = 16#8001；库内容保持不变。
K5 删除时若 recipeID 不存在，置 status = 16#8004；库内容保持不变。
K6 修改时若 recipeID 不存在，置 status = 16#8005；库内容保持不变。
K4 新增时若库已满，置 status = 16#8003。
所给 semantic_warnings、warnings、missing_fields、dialect_requirements 均为空。
ST_Recipe 字段来源：需求中的结构说明及 io_table 字段类型。

【完整形式化规约；有界时序以扫描周期计】
# task: P17
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
C1: G(error -> !(recipeAdded || recipeDeleted || recipeModified))
    -- 出错时不得同时报成功（失败不掩盖）（K2/K3/K4/K5/K6）
C2: G(recipeAdded -> status == 16#0000)
    -- 新增成功的唯一状态码是 16#0000（K2）
C4: G(!(recipeAdded && recipeDeleted))
    -- 同一周期不可能既新增又删除（K1）
C6: G(error -> (error W (addRecipe || deleteRecipe || modifyRecipe || queryRecipe)))
    -- 错误标志保持到下一次请求为止（不得自动消失）（K2/K3/K4）
C10: G[0,0](!error && !recipeAdded && !recipeDeleted && !recipeModified)
    -- 上电当拍无错误、无成功标志（初态）

【语义冲突报告及边界选择】
1. io_table 额外列出 recipeID、ingredientType、ingredientRatio、
   productionTemperature 四个独立 IN，但提供的声明仅将其作为
   ST_Recipe 字段。本实现保留声明接口，通过 recipeIn 访问字段，
   不新增四个独立输入；该接口数据冲突仍然存在。
2. K1 若按所有写入理解，与修改已有配方的要求冲突。
   本实现仅对新增执行空位限制，修改替换已有配方；
   不声称同时满足 K1 的字面广义解释。
3. 同时请求未规定仲裁，而 C4 禁止同拍新增与删除均成功。
   本实现每拍最多处理一个请求，优先级：
   addRecipe > deleteRecipe > modifyRecipe > queryRecipe。
   未选中的请求不排队。
4. 触发方式未规定边沿。本实现采用电平请求：
   每拍均处理当前最高优先级有效请求。
5. 编号 0 为保留空位标记，不视为可查询、删除或修改的配方。
   新增编号 0 拒绝，沿用 16#8002；原题未给专用非法编号错误码。
6. 用户提供的逐周期测试在 cycle 1 要求处理请求并输出成功或错误，
   且查询用例要求使用调用方预置数据库。
   本实现因此不清库、不跳过首次调用。
   C10 按首次调用前的初始化状态解释，由输出声明初值体现；
   若 C10 的时间 0 指首次调用结束后的采样，则与上述测试要求冲突。
   保留该冲突，不声称同时满足两种时间解释。
   需求的空库初态与测试中的预置非空库也存在场景差异；
   数据库初态由调用方或测试夹具建立。
7. 查询失败或无查询时保留上次查询结果，以 error/status 判定结果。
8. 删除仅清除 recipeID，其余字段保留，符合删除原文定义。
9. 运行期间调用方应保持数据库非零编号唯一；
   若外部破坏该不变量，查询、删除和修改选择最小匹配下标，
   新增仍拒绝已有编号。本实现不静默修复外部数据库。
*)

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
    i : INT;
    matchIndex : INT;
    emptyIndex : INT;
END_VAR

recipeAdded := FALSE;
recipeDeleted := FALSE;
recipeModified := FALSE;

IF addRecipe OR deleteRecipe OR modifyRecipe OR queryRecipe THEN
    error := FALSE;
    status := WORD#16#0000;
    matchIndex := 0;
    emptyIndex := 0;

    FOR i := 1 TO 10 DO
        IF recipe[i].recipeID = 0 THEN
            IF emptyIndex = 0 THEN
                emptyIndex := i;
            END_IF;
        ELSE
            IF recipe[i].recipeID = recipeIn.recipeID THEN
                IF matchIndex = 0 THEN
                    matchIndex := i;
                END_IF;
            END_IF;
        END_IF;
    END_FOR;

    IF addRecipe THEN
        IF (recipeIn.recipeID = 0) OR (matchIndex <> 0) THEN
            error := TRUE;
            status := WORD#16#8002;
        ELSIF emptyIndex = 0 THEN
            error := TRUE;
            status := WORD#16#8003;
        ELSE
            recipe[emptyIndex] := recipeIn;
            recipeAdded := TRUE;
        END_IF;

    ELSIF deleteRecipe THEN
        IF matchIndex = 0 THEN
            error := TRUE;
            status := WORD#16#8004;
        ELSE
            recipe[matchIndex].recipeID := 0;
            recipeDeleted := TRUE;
        END_IF;

    ELSIF modifyRecipe THEN
        IF matchIndex = 0 THEN
            error := TRUE;
            status := WORD#16#8005;
        ELSE
            recipe[matchIndex] := recipeIn;
            recipeModified := TRUE;
        END_IF;

    ELSIF queryRecipe THEN
        IF matchIndex = 0 THEN
            error := TRUE;
            status := WORD#16#8001;
        ELSE
            recipeQueryResult := recipe[matchIndex];
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
