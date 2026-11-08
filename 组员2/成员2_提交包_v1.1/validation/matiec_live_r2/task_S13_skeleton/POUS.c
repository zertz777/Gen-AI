#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_S13_init__(FB_S13_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_S13_body__(FB_S13_data__ *data__);
#endif

static void FB_S13_init__(FB_S13_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->LINERUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PARTATMERGE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PARTONMAIN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->JAMSENSOR,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RESETBTN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MODEAUTO,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MAINMOTOR,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MERGEMOTOR,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SPEEDHIGH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->JAMALARM,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATUS,0,retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_S13_body__(FB_S13_data__ *data__) {
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
} // FB_S13_body__() 

#endif




