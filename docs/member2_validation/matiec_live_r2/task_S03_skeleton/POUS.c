#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO_impl.h"
#else
  #include "iec_std_FB_impl.h"
#endif

static void FB_S03_init__(FB_S03_data__ *data__, BOOL retain);
#ifndef __POUS_INIT_ONLY__
static void FB_S03_body__(FB_S03_data__ *data__);
#endif

static void FB_S03_init__(FB_S03_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->DOORSWITCH,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ZONEAOCCUPIED,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ZONEBOCCUPIED,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RESETBTN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ESTOP_NC,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->DRIVEA_RUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->DRIVEB_RUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ALARMLAMP,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATUS,0,retain)
}

#ifndef __POUS_INIT_ONLY__
// Code part
static void FB_S03_body__(FB_S03_data__ *data__) {
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
} // FB_S03_body__() 

#endif




