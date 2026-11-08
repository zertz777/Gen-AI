#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P15_init__(FB_P15_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P15_body__(FB_P15_data__ *data__);
#endif

static void FB_P15_init__(FB_P15_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ESTOP,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OPEMODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVEASTART,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVEBSTART,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVECSTART,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVEDSTART,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MIXMOTORSTART,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTOSTART,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PROCESSMODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LEVELSENSOR,0,retain)
  __INIT_VAR(data__->MIXMOTORCOMPLETE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVEARUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVEBRUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVECRUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->VALVEDRUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MIXMOTORRUN,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P15_body__(FB_P15_data__ *data__) {
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
} // FB_P15_body__() 

#endif




