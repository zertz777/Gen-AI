TYPE ST_Pump :
STRUCT
    priority : INT;
    selection : BOOL;
    RunComd : BOOL;
END_STRUCT
END_TYPE

FUNCTION_BLOCK FB_P07
VAR_INPUT
    mode : BOOL;
    start : BOOL;
    stop : BOOL;
END_VAR
VAR_IN_OUT
    pumpGroup : ARRAY[1..5] OF ST_Pump;
END_VAR
VAR
    firstScan : BOOL := TRUE;
    prevStart : BOOL;
    started : BOOL;
    activePump : ARRAY[1..5] OF BOOL;
    selected : ARRAY[1..5] OF BOOL;
    startEdge : BOOL;
    i : INT;
    n : INT;
    bestIndex : INT;
    bestPriority : INT;
    bestFound : BOOL;
    manualFound : BOOL;
    anyActive : BOOL;
END_VAR

IF stop THEN
    FOR i := 1 TO 5 DO
        pumpGroup[i].RunComd := FALSE;
        activePump[i] := FALSE;
    END_FOR;
    started := FALSE;
END_IF;

IF firstScan THEN
    FOR i := 1 TO 5 DO
        pumpGroup[i].RunComd := FALSE;
        activePump[i] := FALSE;
        selected[i] := FALSE;
    END_FOR;
    started := FALSE;
    prevStart := start;
    firstScan := FALSE;
ELSE
    startEdge := start AND NOT prevStart;

    IF NOT stop THEN
        IF startEdge AND NOT started THEN
            IF mode THEN
                FOR i := 1 TO 5 DO
                    activePump[i] := FALSE;
                    selected[i] := FALSE;
                END_FOR;

                FOR n := 1 TO 3 DO
                    bestFound := FALSE;
                    bestIndex := 0;
                    bestPriority := 0;
                    FOR i := 1 TO 5 DO
                        IF NOT selected[i] THEN
                            IF (NOT bestFound) OR
                               (pumpGroup[i].priority > bestPriority) OR
                               ((pumpGroup[i].priority = bestPriority) AND (i < bestIndex)) THEN
                                bestFound := TRUE;
                                bestIndex := i;
                                bestPriority := pumpGroup[i].priority;
                            END_IF;
                        END_IF;
                    END_FOR;
                    IF bestFound THEN
                        selected[bestIndex] := TRUE;
                        activePump[bestIndex] := TRUE;
                    END_IF;
                END_FOR;
            ELSE
                FOR i := 1 TO 5 DO
                    activePump[i] := FALSE;
                END_FOR;

                manualFound := FALSE;
                FOR i := 1 TO 5 DO
                    IF NOT manualFound AND pumpGroup[i].selection THEN
                        activePump[i] := TRUE;
                        manualFound := TRUE;
                    END_IF;
                END_FOR;
            END_IF;

            anyActive := FALSE;
            FOR i := 1 TO 5 DO
                IF activePump[i] THEN
                    anyActive := TRUE;
                END_IF;
            END_FOR;
            started := anyActive;
        END_IF;

        IF started THEN
            FOR i := 1 TO 5 DO
                pumpGroup[i].RunComd := activePump[i];
            END_FOR;
        ELSE
            FOR i := 1 TO 5 DO
                pumpGroup[i].RunComd := FALSE;
            END_FOR;
        END_IF;
    ELSE
        FOR i := 1 TO 5 DO
            pumpGroup[i].RunComd := FALSE;
        END_FOR;
    END_IF;

    prevStart := start;
END_IF;
END_FUNCTION_BLOCK
