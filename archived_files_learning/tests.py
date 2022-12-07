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