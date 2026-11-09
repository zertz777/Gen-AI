#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P10_init__(FB_P10_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P10_body__(FB_P10_data__ *data__);
#endif

static void FB_P10_init__(FB_P10_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->TEMPERATURESENSORINPUT,0,retain)
  __INIT_VAR(data__->SETTEMPERATURE,0,retain)
  __INIT_VAR(data__->CURRENTTEMPERATURE,0,retain)
  __INIT_VAR(data__->SETTEMPDISPLAY,0,retain)
  __INIT_VAR(data__->HEATERSTATUS,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OVERHEATPROTECTION,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->HEATEROUTPUT,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P10_body__(FB_P10_data__ *data__) {
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
} // FB_P10_body__() 

#endif




