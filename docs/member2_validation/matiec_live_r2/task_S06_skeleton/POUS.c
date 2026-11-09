#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_S06_init__(FB_S06_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_S06_body__(FB_S06_data__ *data__);
#endif

static void FB_S06_init__(FB_S06_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->TEMPPV,0,retain)
  __INIT_VAR(data__->SETTEMP,0,retain)
  __INIT_VAR(data__->SEGMENT,0,retain)
  __INIT_VAR(data__->LOADREDUCEREQ,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->HEATON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FANON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OVERTEMPALARM,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LOADREDUCE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATUS,0,retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_S06_body__(FB_S06_data__ *data__) {
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
} // FB_S06_body__() 

#endif




