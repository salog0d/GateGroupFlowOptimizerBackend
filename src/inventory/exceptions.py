from fastapi import HTTPException, status

LOT_DUPLICATE = {
    "error_code": "LOT_DUPLICATE",
    "detail": "The provided lot_number already exists in the database."
}

LOT_NOT_FOUND = {
    "error_code": "LOT_NOT_FOUND",
    "detail": "The requested inventory lot was not found."
}

INVALID_PRODUCT = {
    "error_code": "INVALID_PRODUCT",
    "detail": "The specified product_id is not recognized in the fixed catalog."
}

INVALID_QUANTITY = {
    "error_code": "INVALID_QUANTITY",
    "detail": "Quantity must be a non-negative integer."
}

DATABASE_ERROR = {
    "error_code": "DATABASE_ERROR",
    "detail": "An unexpected database error occurred."
}

HTTP_LOT_DUPLICATE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail=LOT_DUPLICATE,
)

HTTP_LOT_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=LOT_NOT_FOUND,
)

HTTP_INVALID_PRODUCT = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=INVALID_PRODUCT,
)

HTTP_INVALID_QUANTITY = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=INVALID_QUANTITY,
)

HTTP_DATABASE_ERROR = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail=DATABASE_ERROR,
)
