#!/usr/bin/env python3.1

import time
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


from validator import StableValidator


@dataclass
class AxonProbe:
    times: Dict[int, float]
    validator: StableValidator

    async def probe_single_axon(self, uid: int) -> Tuple[int, float]:
        """
        Probe a single axon and return its UID and probe result (e.g., latency).
        """
        # TODO Implement axon probe functionality
        import random

        probe_result = random.random()

        return uid, probe_result

    def get_last_queried_time(self, uuid: int) -> float:
        # TODO
        return 0.0

    def set_last_queried_time(self, uuid: int) -> None:
        self.times[uuid] = time.time()

    async def probe_local_axons(
        self, n_neurons: int, exclude: Optional[List[int]] = None
    ):
        """
        Probes local axons (e.g. locally connected miner nodes)

        Our main task here will be to query the is_alive functionality, however
        this function could be extended
        """
        axons: Dict[int, float] = {}

        # 1. Get list of UIDs from the validators metagraph
        uids = list(range(self.validator.metagraph.n.item()))

        if exclude is not None:
            uids = [uid for uid in uids if uid not in exclude]

        # 2. Rank by time queried last
        # Assume self.metagraph.last_queried_time is a
        # dictionary mapping UIDs to their last queried time
        uids.sort(key=lambda uid: self.get_last_queried_time(uid, float("inf")))

        # 3. Query the bottom 1.5x N_NEURONS
        neurons_search_count = int(n_neurons * 1.5)
        uids_to_probe = uids[:neurons_search_count]

        # Spawn coroutines for probing the axons
        probe_coroutines = [self.probe_single_axon(uid) for uid in uids_to_probe]

        # 4. Repeat if we have less than N_NEURONS
        while True:
            probe_results = await asyncio.gather(
                *probe_coroutines, return_exceptions=True
            )
            axons = {
                uid: result
                for uid, result in probe_results
                if not isinstance(result, Exception)
            }

            if len(axons) >= n_neurons:
                break

            else:
                # Query additional axons
                additional_uids = uids[len(axons) : len(axons) + neurons_search_count]
                probe_coroutines = [
                    self.probe_single_axon(uid) for uid in additional_uids
                ]

        # 5. Mark a miner as queried (updating its time) if it fails to respond to several IsAlives
        # Assume self.metagraph.update_last_queried_time is a method to update the last queried time for a UID
        for uid, result in probe_results:
            if isinstance(result, Exception):
                # Mark the axon as queried if it failed to respond
                self.set_last_queried_time(uid)

        return axons
