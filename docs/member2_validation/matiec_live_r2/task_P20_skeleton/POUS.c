#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_P20_init__(FB_P20_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_P20_body__(FB_P20_data__ *data__);
#endif

static void FB_P20_init__(FB_P20_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->MODE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FORWARDBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->REVERSEBUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORFEED,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORWASH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORWEIGHT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSORFIRING,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SENSOROUTPUT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->WASHCOMPLETE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->WEIGHTCOMPLETE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->WEIGHT,0,retain)
  __INIT_VAR(data__->FIRINGCOMPLETE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOTORFORWARD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MOTORREVERSE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->KICK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->COMPLETIONLIGHT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FIRINGTEMP,0,retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_P20_body__(FB_P20_data__ *data__) {
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
} // FB_P20_body__() 

#endif




