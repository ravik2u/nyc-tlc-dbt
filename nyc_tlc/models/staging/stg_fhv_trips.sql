with source as (

    select * from {{ source('raw', 'fhv_trips') }}

),

renamed as (

    select
        upper(trim(dispatching_base_num))       as dispatching_base_num,
        upper(trim(Affiliated_base_number))     as affiliated_base_num,
        cast(pickup_datetime  as datetime2(0))  as pickup_at,
        cast(dropOff_datetime as datetime2(0))  as dropoff_at,
        cast(PUlocationID as int)               as pickup_location_id,
        cast(DOlocationID as int)               as dropoff_location_id,
        cast(SR_Flag as int)                    as shared_ride_flag,
        _source_file,
        _loaded_at
    from source

),

keyed as (

    select
        convert(varchar(64), hashbytes('SHA2_256', concat_ws('|',
            dispatching_base_num, pickup_at, dropoff_at,
            pickup_location_id, dropoff_location_id)), 2) as trip_id,
        *
    from renamed

),

deduped as (

    select *,
        row_number() over (partition by trip_id order by _loaded_at desc) as rn
    from keyed

)

select
    trip_id, dispatching_base_num, affiliated_base_num,
    pickup_at, dropoff_at,
    datediff(minute, pickup_at, dropoff_at) as trip_duration_min,
    pickup_location_id, dropoff_location_id, shared_ride_flag,
    _source_file, _loaded_at
from deduped
where rn = 1