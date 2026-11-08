#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_S08_init__(FB_S08_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_S08_body__(FB_S08_data__ *data__);
#endif

static void FB_S08_init__(FB_S08_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->RECIPESELECT,0,retain)
  __INIT_VAR(data__->CHANGEOVERREQ,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PARTHEIGHT,0,retain)
  __INIT_VAR(data__->ESTOP_NC,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ACTIVERECIPE,0,retain)
  __INIT_VAR(data__->SORTLEFT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SORTRIGHT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BUSY,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATUS,0,retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_S08_body__(FB_S08_data__ *data__) {
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
} // FB_S08_body__() 

#endif




