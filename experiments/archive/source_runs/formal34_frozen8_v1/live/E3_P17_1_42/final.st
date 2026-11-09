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
    (* io_table additionally lists these as IN; kept and used as fallback when recipeIn.recipeID = 0 *)
    recipeID : INT;
    ingredientType : INT;
    ingredientRatio : REAL;
    productionTemperature : REAL;
END_VAR
VAR_OUTPUT
    recipeAdded : BOOL;
    recipeDeleted : BOOL;
    recipeModified : BOOL;
    recipeQueryResult : ST_Recipe;
    error : BOOL;
    status : WORD;
END_VAR
VAR_IN_OUT
    recipe : ARRAY[1..10] OF ST_Recipe;
END_VAR
VAR
    prevAdd : BOOL;
    prevDelete : BOOL;
    prevModify : BOOL;
    prevQuery : BOOL;
    initialized : BOOL;
    riseAdd : BOOL;
    riseDelete : BOOL;
    riseModify : BOOL;
    riseQuery : BOOL;
    inputRecipe : ST_Recipe;
    i : INT;
    idx : INT;
    emptyIndex : INT;
    duplicate : BOOL;
    found : BOOL;
END_VAR

IF NOT initialized THEN
    (* C10: power-up scan must have no error and no success flags *)
    recipeAdded := FALSE;
    recipeDeleted := FALSE;
    recipeModified := FALSE;
    error := FALSE;
    status := 16#0000;
    recipeQueryResult.recipeID := 0;
    recipeQueryResult.ingredientType := 0;
    recipeQueryResult.ingredientRatio := 0.0;
    recipeQueryResult.productionTemperature := 0.0;
    prevAdd := FALSE;
    prevDelete := FALSE;
    prevModify := FALSE;
    prevQuery := FALSE;
    initialized := TRUE;
ELSE
    (* success flags are pulse outputs: one scan cycle per successful request *)
    recipeAdded := FALSE;
    recipeDeleted := FALSE;
    recipeModified := FALSE;

    (* rising-edge request detection *)
    riseAdd := addRecipe AND NOT prevAdd;
    riseDelete := deleteRecipe AND NOT prevDelete;
    riseModify := modifyRecipe AND NOT prevModify;
    riseQuery := queryRecipe AND NOT prevQuery;

    prevAdd := addRecipe;
    prevDelete := deleteRecipe;
    prevModify := modifyRecipe;
    prevQuery := queryRecipe;

    (* preserve ST_Recipe mapping; use separate INs only as compatibility fallback *)
    inputRecipe := recipeIn;
    IF inputRecipe.recipeID = 0 AND recipeID <> 0 THEN
        inputRecipe.recipeID := recipeID;
        inputRecipe.ingredientType := ingredientType;
        inputRecipe.ingredientRatio := ingredientRatio;
        inputRecipe.productionTemperature := productionTemperature;
    END_IF;

    IF riseAdd OR riseDelete OR riseModify OR riseQuery THEN
        error := FALSE;
        status := 16#0000;

        IF riseAdd THEN
            duplicate := FALSE;
            emptyIndex := 0;

            IF inputRecipe.recipeID = 0 THEN
                (* 0 denotes an empty slot, so it is not a valid recipe number for add *)
                duplicate := TRUE;
            END_IF;

            FOR i := 1 TO 10 DO
                IF recipe[i].recipeID <> 0 AND recipe[i].recipeID = inputRecipe.recipeID THEN
                    duplicate := TRUE;
                    EXIT;
                END_IF;
                IF recipe[i].recipeID = 0 AND emptyIndex = 0 THEN
                    emptyIndex := i;
                END_IF;
            END_FOR;

            IF duplicate THEN
                error := TRUE;
                status := 16#8002;
            ELSIF emptyIndex = 0 THEN
                error := TRUE;
                status := 16#8003;
            ELSE
                recipe[emptyIndex] := inputRecipe;
                recipeAdded := TRUE;
                error := FALSE;
                status := 16#0000;
            END_IF;

        ELSIF riseDelete THEN
            found := FALSE;
            idx := 0;

            FOR i := 1 TO 10 DO
                IF recipe[i].recipeID <> 0 AND recipe[i].recipeID = inputRecipe.recipeID THEN
                    found := TRUE;
                    idx := i;
                    EXIT;
                END_IF;
            END_FOR;

            IF found THEN
                recipe[idx].recipeID := 0;
                recipe[idx].ingredientType := 0;
                recipe[idx].ingredientRatio := 0.0;
                recipe[idx].productionTemperature := 0.0;
                recipeDeleted := TRUE;
                error := FALSE;
                status := 16#0000;
            ELSE
                error := TRUE;
                status := 16#8004;
            END_IF;

        ELSIF riseModify THEN
            found := FALSE;
            idx := 0;

            FOR i := 1 TO 10 DO
                IF recipe[i].recipeID <> 0 AND recipe[i].recipeID = inputRecipe.recipeID THEN
                    found := TRUE;
                    idx := i;
                    EXIT;
                END_IF;
            END_FOR;

            IF found THEN
                recipe[idx] := inputRecipe;
                recipeModified := TRUE;
                error := FALSE;
                status := 16#0000;
            ELSE
                error := TRUE;
                status := 16#8005;
            END_IF;

        ELSIF riseQuery THEN
            found := FALSE;

            FOR i := 1 TO 10 DO
                IF recipe[i].recipeID <> 0 AND recipe[i].recipeID = inputRecipe.recipeID THEN
                    recipeQueryResult := recipe[i];
                    found := TRUE;
                    EXIT;
                END_IF;
            END_FOR;

            IF found THEN
                error := FALSE;
                status := 16#0000;
            ELSE
                error := TRUE;
                status := 16#8001;
            END_IF;
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
