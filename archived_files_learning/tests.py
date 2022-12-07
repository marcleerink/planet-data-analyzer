def test_get_item_types_i(item_types):
    """test if filled list with item types is returned"""
    client = DataAPIClient()

    response = client.get_item_types(key='id')
    assert response == item_types


def test_get_features_i(geometry, fake_response_small_aoi):
    """
    test if image_features are retrieved from data client and ImageDataFeature 
    generator is returned with correct data.
    """
    start_date = '2022-10-01'
    end_date = '2022-10-02'
    cc = 0.1

    client = DataAPIClient()
    features = list(client.get_features(start_date=start_date,
                                        end_date=end_date,
                                        cc=cc,
                                        geometry=geometry))

    assert len(features) == len(fake_response_small_aoi)
    assert [i.id for i in features] == [str(i["id"]) for i in fake_response_small_aoi]


def test_get_features_filter_i(geometry):
    """test if api response is filtered"""
    start_date = '2022-10-03'
    end_date = '2022-10-05'
    cc = 0.1
    item_types = ['PSScene', 'PSOrthoTile']

    dt_end_date = pd.to_datetime(end_date)
    dt_start_date = pd.to_datetime(start_date)

    client = DataAPIClient()
    image_features_list = list(client.get_features(start_date=start_date,
                                                   end_date=end_date,
                                                   cc=cc,
                                                   geometry=geometry,
                                                   item_types=item_types))

    assert len(image_features_list) >= 1
    assert all(feature.cloud_cover <= cc for feature in image_features_list)
    assert all(pd.to_datetime(feature.time_acquired).tz_localize(
        None) <= dt_end_date for feature in image_features_list)
    assert all(pd.to_datetime(feature.time_acquired).tz_localize(
        None) >= dt_start_date for feature in image_features_list)
    assert all('PS' in feature.item_type_id for feature in image_features_list)


def test_query_lat_lon_sat_images_i(db_session, setup_models):
    # arrange
    sat_images = db_session.query(db.SatImage).all()

    # act
    lat_lon = query.query_lat_lon_from_images(sat_images)

    # assert
    assert lat_lon == [[55.474220203855445, 8.804454520157185]]

def test_query_asset_types_from_image(fake_image):

    asset_types = query.query_asset_types_from_image(fake_image)

    assert asset_types == ['asset1', 'asset2']
def test_query_land_cover_class_from_image(fake_image):

    land_cover_class = query.query_land_cover_class_from_image(fake_image)

    assert land_cover_class == ['fake_land_cover_class']
    
def test_create_images_df(fake_image):
    images_df = query.create_images_df([fake_image])

    assert isinstance(images_df, pd.DataFrame)
    assert images_df['id'][0] == fake_image.id
    assert images_df['cloud_cover'][0] == fake_image.cloud_cover
    assert images_df['pixel_res'][0] == fake_image.satellites.pixel_res
    assert images_df['time_acquired'][0] == fake_image.time_acquired.strftime("%Y-%m-%d %H:%M:%S")
    assert images_df['sat_name'][0] == fake_image.satellites.name
    assert images_df['area_sqkm'][0] == fake_image.area_sqkm


def test_create_images_geojson(fake_image):

    images_geojson = query.create_images_geojson([fake_image])

    assert images_geojson['features'][0]['properties']['id'] == fake_image.id
    assert images_geojson['features'][0]['properties']['cloud_cover'] == fake_image.cloud_cover
    assert images_geojson['features'][0]['properties']['pixel_res'] == fake_image.satellites.pixel_res
    assert images_geojson['features'][0]['properties']['time_acquired'] == fake_image.time_acquired.strftime(
        "%Y-%m-%d %H:%M:%S")
    assert images_geojson['features'][0]['properties']['sat_name'] == fake_image.satellites.name
    assert images_geojson['features'][0]['properties']['asset_types'] == [i.id for i in fake_image.item_types.assets]