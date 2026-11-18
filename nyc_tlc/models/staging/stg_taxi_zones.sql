select
    cast(LocationID as int)  as location_id,
    trim(Borough)            as borough,
    trim(Zone)               as zone_name,
    trim(service_zone)       as service_zone
from {{ ref('taxi_zone_lookup') }}