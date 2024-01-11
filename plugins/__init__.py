class IOPlugin:
    async def get(self) -> str:
        """Get data from output"""
        raise NotImplementedError()

    async def put(self, data: str):
        """Put data to input"""
        raise NotImplementedError()

    async def start(self):
        """Start the IO"""
        raise NotImplementedError()

    async def stop(self):
        """Stop the IO"""
        raise NotImplementedError()
