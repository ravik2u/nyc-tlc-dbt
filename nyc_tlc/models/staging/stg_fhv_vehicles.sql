with source as (

    select * from {{ source('raw', 'fhv_vehicles') }}

),

renamed as (

    select
        upper(trim(vehicle_license_number))       as vehicle_license_number,
        upper(trim(base_number))                  as base_num,
        trim(base_name)                           as base_name,
        trim(base_type)                           as base_type,
        trim(license_type)                        as license_type,
        upper(trim(dmv_license_plate_number))     as plate_number,
        try_cast(vehicle_year as int)             as vehicle_year,
        case when upper(trim(wheelchair_accessible)) in ('WAV', 'Y', 'YES')
             then 1 else 0 end                    as is_wheelchair_accessible,
        case when upper(trim(active)) = 'YES'
             then 1 else 0 end                    as is_active,
        try_cast(expiration_date as date)         as license_expiration_date,
        try_cast(last_date_updated as date)       as source_updated_date,
        _source_file,
        _loaded_at
    from source

)

select * from renamed