class Box:
    VAT_DUE_SALES = '1'
    VAT_DUE_ACQUISITIONS = '2'
    TOTAL_VAT_DUE = '3'
    VAT_RECLAIMED_ON_INPUTS = '4'
    NET_VAT_DUE = '5'
    TOTAL_VALUE_SALES = '6'
    TOTAL_VALUE_PURCHASES = '7'
    TOTAL_VALUE_GOODS_SUPPLIED = '8'
    TOTAL_VALUE_ACQUISITIONS = '9'

    @staticmethod
    def all_box_codes():
        """Return immutable set of all the box codes, each as a string"""
        return frozenset({'1', '2', '3', '4', '5', '6', '7', '8', '9'})

    @staticmethod
    def computed_box_codes():
        """Return immutable set of the box codes that are computed as strings"""
        # TODO compute from dictionary
        return frozenset({
            Box.TOTAL_VAT_DUE,
            Box.NET_VAT_DUE,
        })

    @staticmethod
    def compute_all(known_boxes):
        """Return dictionary of box values, including those computed, from known_boxes."""
        return {
            boxcode: Box._compute(known_boxes, boxcode)
            for boxcode in Box.all_box_codes()
        }

    @staticmethod
    def _compute(known_boxes, boxcode):
        def box_computer(code):
            computed_boxes = {
                Box.TOTAL_VAT_DUE: lambda boxes: (
                    Box._compute(boxes, Box.VAT_DUE_SALES)
                    + Box._compute(boxes, Box.VAT_DUE_ACQUISITIONS)
                ),
                Box.NET_VAT_DUE: lambda boxes: \
                    abs(Box._compute(boxes, Box.TOTAL_VAT_DUE)
                        - Box._compute(boxes, Box.VAT_RECLAIMED_ON_INPUTS))
            }
            return computed_boxes.get(code, lambda boxes: boxes[code])
        return box_computer(boxcode)(known_boxes)
