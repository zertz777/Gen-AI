#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P01_init__(FB_P01_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P01_body__(FB_P01_data__ *data__);
#endif

static void FB_P01_init__(FB_P01_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->BOTTLESENSOR,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLEANINGCONFIRMBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FILLINGCONFIRMBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CAPPINGCONFIRMBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PACKINGCONFIRMBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FINISHEDBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PUMP_MOTOR,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FILLING_VALVE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CAPPING_MACHINE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PACKING_MACHINE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->COMPLETION_LIGHT,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P01_body__(FB_P01_data__ *data__) {
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
} // FB_P01_body__() 

#endif




