#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P06_init__(FB_P06_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P06_body__(FB_P06_data__ *data__);
#endif

static void FB_P06_init__(FB_P06_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->DO_LOW,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AERATION_E_STOP_NC,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BLOWER_RUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AERATION_BLOWER_CYCLE_COUNT,0,retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P06_body__(FB_P06_data__ *data__) {
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
} // FB_P06_body__() 

#endif




