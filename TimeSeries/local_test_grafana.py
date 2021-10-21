import timeSeriesFunctions

created_streaming_dashboard_id, dashboard_name, panel_ids = timeSeriesFunctions.create_streaming_dashboard_on_grafana(
    ["test1", "test2"], 5, "1s")
annotation_result = timeSeriesFunctions.add_annotation_to_panel(created_streaming_dashboard_id, panel_ids[0], [
    1616526530 * 1000, 1616526580 * 1000], ["desc1", "desc2"])
annotation_result2 = timeSeriesFunctions.add_annotation_to_panel(created_streaming_dashboard_id, panel_ids[1], [
    1616526530 * 1000, 1616526580 * 1000], ["desc3", "desc4"])
print(annotation_result)
print(annotation_result2)
