```
>>> from astroquery.esa.xmm_newton import XMMNewton
>>> XMMNewton.get_tables()
INFO: Retrieving tables... [astroquery.utils.tap.core]
INFO: Parsing tables... [astroquery.utils.tap.core]
INFO: Done. [astroquery.utils.tap.core]
['public.dual', 'tap_config.coord_sys', 'tap_config.properties', 'tap_schema.columns',
 'tap_schema.key_columns', 'tap_schema.keys', 'tap_schema.schemas',
 'tap_schema.tables', 'xsa.v_all_observations', 'xsa.v_epic_source',
 'xsa.v_epic_source_cat', 'xsa.v_epic_xmm_stack_cat', 'xsa.v_exposure',
 'xsa.v_instrument_mode', 'xsa.v_om_source', 'xsa.v_om_source_cat',
 'xsa.v_proposal', 'xsa.v_proposal_observation_info', 'xsa.v_publication',
 'xsa.v_publication_observation', 'xsa.v_publication_slew_observation',
 'xsa.v_public_observations', 'xsa.v_public_observations_new_odf_ingestion',
 'xsa.v_public_observations_new_pps_ingestion', 'xsa.v_rgs_source',
 'xsa.v_slew_exposure', 'xsa.v_slew_observation', 'xsa.v_slew_source',
 'xsa.v_slew_source_cat', 'xsa.v_target_type', 'xsa.v_uls_exposure_image',
 'xsa.v_uls_slew_exposure_image']
```