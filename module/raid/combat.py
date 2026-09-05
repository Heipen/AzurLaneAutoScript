from module.combat.assets import BATTLE_STATUS_C, BATTLE_STATUS_D, EXP_INFO_C, EXP_INFO_D
from module.combat.combat import Combat
from module.guild.assets import BATTLE_STATUS_CF, EXP_INFO_CF
from module.logger import logger


class RaidCombat(Combat):
    @property
    def raid_ignore_failure(self):
        """
        Raid_IgnoreFailure (ignoring defeat) for sunk fleet affinity farming.
        """
        return getattr(self.config, 'Raid_IgnoreFailure', False)

    def handle_battle_status(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if not self.raid_ignore_failure:
            # C/D rank means fleet sunk, treat as defeat
            if self.appear(BATTLE_STATUS_C, interval=self.battle_status_click_interval) \
                    or self.appear(BATTLE_STATUS_D, interval=self.battle_status_click_interval):
                logger.warning('Battle status C/D, keep as defeat (disable Raid_IgnoreFailure)')
                return False
        if super().handle_battle_status(drop=drop):
            return True
        if self.appear(BATTLE_STATUS_CF, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_CF)
            return True

        return False

    def handle_get_items(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if super().handle_get_items(drop=drop):
            self.interval_reset(BATTLE_STATUS_CF)
            return True
        else:
            return False

    def handle_exp_info(self):
        """
        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if super().handle_exp_info():
            return True
        if self.raid_ignore_failure:
            # Click exp info popup on defeated settlement
            if self.appear_then_click(EXP_INFO_C):
                self.device.sleep((0.25, 0.5))
                return True
            if self.appear_then_click(EXP_INFO_D):
                self.device.sleep((0.25, 0.5))
                return True
        if self.appear_then_click(EXP_INFO_CF):
            self.device.sleep((0.25, 0.5))
            return True

        return False
