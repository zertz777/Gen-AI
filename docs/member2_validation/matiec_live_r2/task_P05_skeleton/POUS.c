#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P05_init__(FB_P05_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P05_body__(FB_P05_data__ *data__);
#endif

static void FB_P05_init__(FB_P05_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->GAP_EXCEEDED,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->WELD_E_STOP_NC,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->DEBOUNCETIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->OPERATOR_ALERT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->WELD_SOFT_START_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P05_body__(FB_P05_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  goto __end;

  goto __end;

__end:
  return;
} // FB_P05_body__() 

#endif




