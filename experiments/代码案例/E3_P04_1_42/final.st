FUNCTION_BLOCK FB_P04
VAR_INPUT
    VISCOSITY_OK : BOOL;
    PASTE_E_STOP_NC : BOOL;
    DebounceTime : TIME;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    VFD_RUN : BOOL;
    PUMP_MAINT_DUE : BOOL;
    PUMP_RUNTIME_ACC : LTIME;
END_VAR
VAR
    Initialized : BOOL := FALSE;
    ViscosityValid : BOOL := FALSE;
    DebounceElapsed : LTIME := LTIME#0s;
    CycleTimeLT : LTIME;
    DebounceTimeLT : LTIME;
    CycleTimeValid : BOOL;
END_VAR

IF NOT Initialized THEN
    VFD_RUN := FALSE;
    PUMP_MAINT_DUE := FALSE;
    PUMP_RUNTIME_ACC := LTIME#0s;
    ViscosityValid := FALSE;
    DebounceElapsed := LTIME#0s;
    Initialized := TRUE;
ELSE
    CycleTimeLT := TIME_TO_LTIME(CycleTime);
    DebounceTimeLT := TIME_TO_LTIME(DebounceTime);
    CycleTimeValid := (CycleTime > T#0s);

    IF NOT VISCOSITY_OK THEN
        ViscosityValid := FALSE;
        DebounceElapsed := LTIME#0s;
    END_IF;

    IF NOT PASTE_E_STOP_NC THEN
        VFD_RUN := FALSE;
        IF NOT ViscosityValid THEN
            DebounceElapsed := LTIME#0s;
        END_IF;
    ELSIF NOT VISCOSITY_OK THEN
        VFD_RUN := FALSE;
    ELSE
        IF DebounceTime > T#0s THEN
            IF ViscosityValid THEN
                VFD_RUN := TRUE;
            ELSE
                IF CycleTimeValid THEN
                    DebounceElapsed := DebounceElapsed + CycleTimeLT;
                END_IF;
                IF DebounceElapsed >= DebounceTimeLT THEN
                    ViscosityValid := TRUE;
                    VFD_RUN := TRUE;
                ELSE
                    VFD_RUN := FALSE;
                END_IF;
            END_IF;
        ELSE
            VFD_RUN := FALSE;
            ViscosityValid := FALSE;
            DebounceElapsed := LTIME#0s;
        END_IF;
    END_IF;

    IF VFD_RUN AND CycleTimeValid THEN
        PUMP_RUNTIME_ACC := PUMP_RUNTIME_ACC + CycleTimeLT;
    END_IF;

    IF PUMP_RUNTIME_ACC >= LTIME#500h THEN
        PUMP_MAINT_DUE := TRUE;
    END_IF;
END_IF;
END_FUNCTION_BLOCK
