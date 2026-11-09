#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P19_init__(FB_P19_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P19_body__(FB_P19_data__ *data__);
#endif

static void FB_P19_init__(FB_P19_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->MANUALMODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SINGLESTEPMODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SINGLECYCLEMODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CONTINUOUSMODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->EMERGENCYSTOP,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->START,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->DOWNBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->UPBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LEFTBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RIGHTBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->GRIPBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RELEASEBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->DOWNLIMITSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->UPLIMITSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LEFTLIMITSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RIGHTLIMITSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->GRIPLIMITSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RELEASELIMITSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOVEDOWN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOVEUP,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOVELEFT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOVERIGHT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ACTIVATEGRIP,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ACTIVATERELEASE,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P19_body__(FB_P19_data__ *data__) {
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
} // FB_P19_body__() 

#endif




