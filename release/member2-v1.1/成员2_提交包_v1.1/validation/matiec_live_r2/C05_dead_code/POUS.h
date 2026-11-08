#ifdef  DISABLE_EN_ENO_PARAMETERS
  #include "iec_std_FB_no_ENENO.h"
#else
  #include "iec_std_FB.h"
#endif

__DECLARE_FB_TYPE(FB_AGENTPROBEDEADCODE,
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,Y)


)

