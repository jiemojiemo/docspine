from docspine.models import AssetRef, DocumentNode


def test_document_node_tracks_children_and_assets():
    asset = AssetRef(
        asset_id="figure-1",
        asset_type="image",
        path="assets/figure-1.png",
        caption="Revenue chart",
        source_pages=[3],
    )
    child = DocumentNode(
        node_id="child",
        title="Child",
        slug="child",
        level=1,
        summary="child summary",
    )
    root = DocumentNode(
        node_id="root",
        title="Root",
        slug="root",
        level=0,
        summary="root summary",
        children=[child],
        assets=[asset],
    )

    assert root.children[0].node_id == "child"
    assert root.assets[0].asset_type == "image"
