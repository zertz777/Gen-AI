#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P11_init__(FB_P11_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P11_body__(FB_P11_data__ *data__);
#endif

static void FB_P11_init__(FB_P11_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->MODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FORWARDBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->REVERSEBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORA,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORB,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORC,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BUTTONA,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BUTTONB,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BUTTONC,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOTORFORWARD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOTORREVERSE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->COMPLETIONLIGHT,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P11_body__(FB_P11_data__ *data__) {
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
} // FB_P11_body__() 

#endif




