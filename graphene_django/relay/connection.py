from typing import Dict, List, Optional, Tuple

from django.db.models.query import QuerySet
from graphql_relay import (
    Connection,
    Edge,
    PageInfo,
    SizedSliceable,
    cursor_to_offset,
    offset_to_cursor,
)

from ..utils import GRAPHQL_SYNC_DATALOADERS_INSTALLED, get_info_cache_key

if GRAPHQL_SYNC_DATALOADERS_INSTALLED:
    from graphql_sync_dataloaders import SyncFuture


def connection_from_sized_sliceable(
    sized_sliceable: SizedSliceable,
    args: Dict,
    info=None,
    connection_type=Connection,
    edge_type=Edge,
    page_info_type=PageInfo,
):
    args = args or {}
    before: Optional[str] = args.get("before")
    after: Optional[str] = args.get("after")
    first: Optional[int] = args.get("first")
    last: Optional[int] = args.get("last")

    # Allowed combinations are:
    # - first and/or after
    # - last and/or before

    if first and last:
        raise ValueError("Mixing 'first' and 'last' is not supported.")

    if before and after:
        raise ValueError("Mixing 'before' and 'after' is not supported.")

    if first and before:
        raise ValueError("Mixing 'first' and 'before' is not supported.")

    if last and after:
        raise ValueError("Mixing 'last' and 'after' is not supported.")

    if (first, after, last, before) == (None, None, None, None):
        handle_result = _handle_no_args(
            sized_sliceable=sized_sliceable,
            info=info,
            edge_type=edge_type,
        )

    elif first is not None or after is not None:
        handle_result = _handle_first_after(
            sized_sliceable=sized_sliceable,
            first=first,
            after=after,
            info=info,
            edge_type=edge_type,
        )

    elif last is not None or before is not None:
        handle_result = _handle_last_before(
            sized_sliceable=sized_sliceable,
            last=last,
            before=before,
            edge_type=edge_type,
        )

    else:
        raise ValueError(f"Unreachable: {args}")

    def create_connection(handle_result: Tuple[List[Edge], bool, bool]):
        (
            edges,
            has_previous_page,
            has_next_page,
        ) = handle_result

        first_edge_cursor: Optional[str] = edges[0].cursor if edges else None
        last_edge_cursor: Optional[str] = edges[-1].cursor if edges else None

        return connection_type(
            edges=edges,
            pageInfo=page_info_type(
                startCursor=first_edge_cursor,
                endCursor=last_edge_cursor,
                hasPreviousPage=has_previous_page,
                hasNextPage=has_next_page,
            ),
        )

    if GRAPHQL_SYNC_DATALOADERS_INSTALLED and isinstance(handle_result, SyncFuture):
        return handle_result.then(create_connection)

    return create_connection(handle_result)


def _handle_no_args(
    sized_sliceable: SizedSliceable,
    edge_type,
    info=None,
) -> Tuple[List, bool, bool]:
    """Handle the case where no arguments are provided."""

    def compute_edges(result):
        edges = [
            edge_type(
                node=node,
                cursor=offset_to_cursor(index),
            )
            for index, node in enumerate(result)
        ]

        return (
            edges,
            False,
            False,
        )

    try:
        dataloaders_context = info.context.dataloaders
    except AttributeError:
        pass
    else:
        if isinstance(dataloaders_context, dict) and isinstance(
            sized_sliceable, QuerySet
        ):
            dataloader_key = get_info_cache_key(info)
            if dataloader_key in dataloaders_context:
                return (
                    dataloaders_context[dataloader_key]
                    .load((sized_sliceable, None, None))
                    .then(compute_edges)
                )

            raise RuntimeError(f"Could not find dataloader for {dataloader_key}")

    return compute_edges(sized_sliceable)


def _handle_first_after(
    sized_sliceable: SizedSliceable,
    first: Optional[int],
    after: Optional[str],
    edge_type,
    info=None,
) -> Tuple[List, bool, bool]:
    """Handle the `first` and `after` arguments."""

    if first is not None and first < 0:
        raise ValueError("Argument 'first' must be a non-negative integer.")

    # If defined, convert `after` cursor into an offset.
    after_offset: Optional[int] = cursor_to_offset(after) if after else None

    # Calculate the `start_offset`:
    # If `after` is not provided, start at the beginning of the slice.
    # Otherwise, start right past the `after` cursor.
    start_offset: int = 0 if after_offset is None else after_offset + 1

    # Calculate the `end_offset`:
    # if `first` is not provided, then set `end_offset` to None
    # Otherwise, set it to `start_offset` + `first`
    end_offset: Optional[int]
    if first is None:
        end_offset = None
    else:
        end_offset = start_offset + (first or 0)

    start: Optional[int]
    stop: Optional[int]

    if end_offset is None:
        start = start_offset
        stop = None

        def compute_slice(trimmed_slice):
            has_previous_page: bool = start_offset > 0
            has_next_page: bool = False

            return trimmed_slice, has_previous_page, has_next_page

    else:
        # Slice off one more than we will be returning
        start = start_offset
        stop = end_offset + 1

        def compute_slice(intermediate_slice):
            # Keep intermediate `intermediate_slice_length` variable to force QuerySet evaluation.
            intermediate_slice_length: int = len(intermediate_slice)

            trimmed_slice: SizedSliceable = intermediate_slice[
                : end_offset - start_offset
            ]
            trimmed_slice_length: int = len(trimmed_slice)

            has_next_page: bool = intermediate_slice_length > trimmed_slice_length

            # If the start offset is greater than zero, there is a previous page.
            # However, if the provided `after` cursor is outside the bounds of the slice,
            # enforce that `has_previous_page` is `True`.
            has_previous_page: bool = start_offset > 0

            return trimmed_slice, has_previous_page, has_next_page

    def compute_edges(result):
        trimmed_slice, has_previous_page, has_next_page = result

        edges = [
            edge_type(
                node=node,
                cursor=offset_to_cursor(start_offset + index),
            )
            for index, node in enumerate(trimmed_slice)
        ]

        return (
            edges,
            has_previous_page,
            has_next_page,
        )

    if (
        isinstance(sized_sliceable, QuerySet)
        and info is not None
        and hasattr(info, "context")
        and hasattr(info.context, "dataloaders")
        and isinstance(info.context.dataloaders, dict)
    ):
        dataloader_key = get_info_cache_key(info)
        if dataloader_key in info.context.dataloaders:
            return (
                info.context.dataloaders[dataloader_key]
                .load((sized_sliceable, start, stop))
                .then(compute_slice)
                .then(compute_edges)
            )

        raise RuntimeError(f"Could not find dataloader for {dataloader_key}")

    return compute_edges(compute_slice(sized_sliceable[start:stop]))


def _handle_last_before(
    sized_sliceable: SizedSliceable,
    last: Optional[int],
    before: Optional[str],
    edge_type=Edge,
) -> Tuple[List, bool, bool]:
    """Handle the `last` and `before` arguments."""

    if last is not None and last < 0:
        raise ValueError("Argument 'last' must be a non-negative integer.")

    # If defined, convert `before` cursor into an offset.
    before_offset: Optional[int] = cursor_to_offset(before) if before else None

    if isinstance(sized_sliceable, QuerySet):
        array_length = sized_sliceable.count()
    else:
        array_length = len(sized_sliceable)

    # Calculate the `end_offset`:
    # If `before` is provided, use it as `end_offset` (cropping it to the bounds of the slice).
    # Otherwise, the `end_offset` is the end of the slice.
    end_offset: int
    if before_offset is not None:
        if before_offset < 0:
            before_offset = 0
        end_offset = min(before_offset, array_length)
    else:
        end_offset = array_length

    # Calculate the `start_offset`:
    # If `last` is not provided, then set `start_offset` to None
    # Otherwise, set it to `end_offset` - `last` or 0 (whichever is greater)
    start_offset: Optional[int]
    if last is None:
        start_offset = 0
    else:
        start_offset: int = max(end_offset - last, 0)

    trimmed_slice: SizedSliceable = sized_sliceable[start_offset:end_offset]

    has_previous_page: bool = start_offset > 0

    has_next_page: bool = end_offset < array_length
    if before_offset is not None and before_offset < 0:
        has_next_page = True

    edges = [
        edge_type(
            node=node,
            cursor=offset_to_cursor(start_offset + index),
        )
        for index, node in enumerate(trimmed_slice)
    ]

    return (
        edges,
        has_previous_page,
        has_next_page,
    )
