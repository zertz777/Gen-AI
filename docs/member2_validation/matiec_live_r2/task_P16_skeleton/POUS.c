#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P16_init__(FB_P16_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P16_body__(FB_P16_data__ *data__);
#endif

static void FB_P16_init__(FB_P16_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->PROCESSLENGTH,0,retain)
  __INIT_VAR(data__->SENSOR1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSOR2,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSOR3,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSOR4,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSOR5,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATION1START,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATION2COMPLETE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATION3COMPLETE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATION4COMPLETE,__BOOL_LITERAL(FALSE),retain)
  {
    static const __ARRAY_OF_USINT_8 temp = {{{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}}};
    __SET_VAR(data__->,PROCESSSEQUENCE,,temp);
  }
  __INIT_VAR(data__->CONVEYORLEFT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CONVEYORRIGHT,__BOOL_LITERAL(FALSE),retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P16_body__(FB_P16_data__ *data__) {
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
} // FB_P16_body__() 

#endif




