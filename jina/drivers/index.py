__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import BaseExecutableDriver
from .helper import extract_chunks


class BaseIndexDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'add', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class VectorIndexDriver(BaseIndexDriver):
    """Extract chunk-level embeddings and add it to the executor

    """

    def __call__(self, *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = extract_chunks(self.docs, self.chunks,
                                                                             self.req.filter_by,
                                                                             embedding=True)

        if no_chunk_docs:
            self.pea.logger.warning(f'these docs contain no chunk: {no_chunk_docs}')

        if bad_chunk_ids:
            self.pea.logger.warning(f'these bad chunks can not be added: {bad_chunk_ids}')

        if chunk_pts:
            self.exec_fn(np.array([c.chunk_id for c in chunk_pts]), np.stack(embed_vecs))


class KVIndexDriver(BaseIndexDriver):
    """Serialize the documents/chunks in the request to key-value JSON pairs and write it using the executor

    Number of key-value pairs depends on the ``level``

         - ``level=chunk``: D x C
         - ``level=doc``: D
         - ``level=all``: D x C + D

    where:
        - D is the number of queries
        - C is the number of chunks per query/doc
    """

    def __init__(self, level: str, *args, **kwargs):
        """

        :param level: index level "chunk" or "doc", or "all"
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.level = level

    def __call__(self, *args, **kwargs):
        if self.level == 'doc':
            content = self.docs
        elif self.level == 'chunk':
            content = (c for d in self.docs for c in self.chunks(d) if
                       (not self.req.filter_by or c.field_name in self.req.filter_by))
        else:
            raise TypeError(f'level={self.level} is not supported, must choose from "chunk" or "doc" ')
        if content:
            self.exec_fn(content)
