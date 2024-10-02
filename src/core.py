import cloudscraper
import asyncio
import random
import aiohttp
from colorama import *
import json
from datetime import datetime
from . import *

init(autoreset=True)
cfg = read_config()
class GameSession:
    def __init__(self, acc_data, tgt_score, prxy=None):
        self.b_url = "https://tonclayton.fun"
        self.s_id = None
        self.a_data = acc_data
        self.hdrs = get_headers(self.a_data)
        self.c_score = 0
        self.t_score = tgt_score
        self.inc = 10
        self.pxy = prxy

        self.scraper = cloudscraper.create_scraper()  
        if self.pxy:
            self.scraper.proxies = {
                'http': f'http://{self.pxy}',
                'https': f'http://{self.pxy}',
            }

    @staticmethod
    def fmt_ts(ts):
        dt = datetime.fromisoformat(ts[:-1])
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    async def start(self):
        lg_url = f"{self.b_url}/api/user/auth"
        while True:
            try:
                resp = self.scraper.post(lg_url, headers=self.hdrs, json={})
                if resp.status_code == 200:
                    usr_data = resp.json()
                    usr = usr_data.get('user', {})
                    log(hju + f"Proxy: {pth}{self.pxy or 'No proxy used'}")
                    log(htm + "~" * 38)
                    log(bru + f"Username: {pth}{usr.get('username', 'N/A')}")
                    log(hju + f"Points: {pth}{usr.get('tokens', 'N/A'):,.0f} {hju}| XP: {pth}{usr.get('current_xp', 'N/A')}")
                    log(hju + f"Level: {pth}{usr.get('level', 'N/A')} {hju}| Tickets: {pth}{usr.get('daily_attempts', 0)}")
                    await self.check_in()
                    break  
                else:
                    log(mrh + f"Login failed Retrying...")
                    await asyncio.sleep(2) 
            except Exception as e:
                log(mrh + f"Exception during login: {e}. Retrying...")
                await asyncio.sleep(2)  

    async def check_in(self):
        lg_url = f"{self.b_url}/api/user/daily-claim"
        try:
            resp = self.scraper.post(lg_url, headers=self.hdrs, json={})
            if resp.status_code == 200:
                res = resp.json()
                daily_attempts = res.get('daily_attempts', 0)
                consecutive_days = res.get('consecutive_days', 0)
                log(hju + f"Success claim daily check-in")
                log(hju + f"Daily Attempts: {pth}{daily_attempts}{hju}, Consecutive Days: {pth}{consecutive_days}")
            elif resp.status_code == 400:
                log(kng + f"You have already check-in today!")
            else:
                log(mrh + f"Failed to claim daily reward. {resp.status_code}")
                await asyncio.sleep(2)
        except Exception as e:
            log(mrh + f"Exception during daily claim: {e}")
            await asyncio.sleep(2)

    async def run_g(self):
        with open('config.json', 'r') as cf:
            cfg = json.load(cf)

        g_tickets = cfg.get("game_ticket_to_play", 1)
        for ticket in range(g_tickets):
            game_choice = random.choice(['stack', 'tiles'])
            log(hju + f"Play {pth}{game_choice} {hju}with ticket {pth}{ticket + 1}/{g_tickets}")

            if game_choice == 'stack':
                await self.play_stack_game()
            else:
                await self.play_tiles_game()

    async def play_stack_game(self):
        st_url = f"{self.b_url}/api/stack/start-game"
        resp = self.scraper.post(st_url, headers=self.hdrs, json={})
        if "no daily attempts left" in resp.text:
            log(kng + f"Stack game: ticket attempts are over")
            return None
        elif resp.status_code == 200:
            self.s_id = resp.json().get("session_id")
            log(bru + f"Stack game: {hju}started{pth} {self.s_id}")
        else:
            error_message = resp.json().get('error', 'Unknown error')
            log(mrh + f"Stack game: start failed {pth}{error_message}")
            return

        self.c_score = 0
        while self.c_score < self.t_score:
            self.c_score += self.inc
            up_url = f"{self.b_url}/api/stack/update-game"
            resp = self.scraper.post(up_url, headers=self.hdrs, json={"score": self.c_score})
            if resp.status_code == 200:
                log(bru + f"Stack game - {hju}update score: {pth}{self.c_score}")
            else:
                log(mrh + f"Stack game - update score failed!")

            await countdown_timer(random.randint(5, 7))

        en_url = f"{self.b_url}/api/stack/end-game"
        payload = {"score": self.c_score, "multiplier": 1}
        resp = self.scraper.post(en_url, headers=self.hdrs, json=payload)
        if resp.status_code == 200:
            res = resp.json()
            log(hju + f"Stack game has ended successfully")
            log(hju + f"XP Earned: {pth}{res['xp_earned']} {hju}| Points: {pth}{res['earn']}")
            await countdown_timer(5)
        else:
            error_message = resp.json().get('error', 'Unknown error')
            log(mrh + f"End session failed: {htm}{error_message}")

    async def play_tiles_game(self):
        start_url = f"{self.b_url}/api/game/start"
        resp = self.scraper.post(start_url, headers=self.hdrs, json={})
        if "No game attempts available" in resp.text:
            log(kng + f"Tiles game: ticket attempts are over")
            return None
        elif resp.status_code == 200:
            log(bru + f"Tiles game: {hju}started successfully")
        else:
            error_message = resp.json().get('error', 'Unknown error')
            log(mrh + f"Tiles game: failed to start {pth}{error_message}")
            return

        max_tile = 2
        updates = random.randint(7, 12)

        for _ in range(updates):
            save_url = f"{self.b_url}/api/game/save-tile"
            payload = {"maxTile": max_tile}
            resp = self.scraper.post(save_url, headers=self.hdrs, json=payload)
            if resp.status_code == 200:
                log(bru + f"Tiles game - {hju}update score: {pth}{max_tile}")
                max_tile *= 2
            else:
                log(mrh + f"Tiles game - update failed!")
            
            await countdown_timer(random.randint(5, 7))

        end_url = f"{self.b_url}/api/game/over"
        end_payload = {"multiplier": 1}
        resp = self.scraper.post(end_url, headers=self.hdrs, json=end_payload)
        if resp.status_code == 200:
            res = resp.json()
            log(hju + f"Tiles game has ended successfully")
            log(hju + f"XP Earned: {pth}{res['xp_earned']} | Points: {pth}{res['earn']}")
            await countdown_timer(5)
        else:
            error_message = resp.json().get('error', 'Unknown error')
            log(mrh + f"End tiles game failed: {pth}{error_message}")

    async def cpl_and_clm_tsk(self, tsk_type='daily'):
        if tsk_type == 'daily':
            t_url = f"{self.b_url}/api/tasks/daily-tasks"
        elif tsk_type == 'default':
            t_url = f"{self.b_url}/api/tasks/default-tasks"
        elif tsk_type == 'super':
            t_url = f"{self.b_url}/api/tasks/super-tasks"
        elif tsk_type == 'partner':
            t_url = f"{self.b_url}/api/tasks/partner-tasks"
        else:
            log(mrh + f"Unknown task type: {tsk_type}")
            return

        await countdown_timer(random.randint(3, 4))
        
        for attempt in range(3):
            resp = self.scraper.get(t_url, headers=self.hdrs)
            if resp.status_code == 200:
                if not resp.text:
                    log(mrh + "Received empty response from the server.")
                    return
                try:
                    tasks = resp.json()
                except ValueError:
                    log(mrh + f"Received non-JSON response: {resp.text}")
                    return
                break
            else:
                log(mrh + f"Failed to retrieve {pth}{tsk_type} {mrh}tasks (Attempt {attempt + 1})")
                await asyncio.sleep(1)
                if attempt == 2:
                    return 

        for t in tasks:
            t_id = t['task_id']
            if not t.get('is_completed', False):
                cmp_url = f"{self.b_url}/api/tasks/complete"
                cmp_resp = self.scraper.post(cmp_url, headers=self.hdrs, json={"task_id": t_id})
                if cmp_resp.status_code == 200:
                    log(hju + f"Completed {pth}{tsk_type}{hju} task: {pth}{t['task']['title']}")
                    wait_time = max(random.randint(4, 6), 1)
                    await countdown_timer(wait_time)
                    clm_url = f"{self.b_url}/api/tasks/claim"
                    clm_resp = self.scraper.post(clm_url, headers=self.hdrs, json={"task_id": t_id})
                    if clm_resp.status_code == 200:
                        clm_data = clm_resp.json()
                        log(hju + f"Claimed {pth}{t['task']['title']} {hju}Successfully | Reward: {pth}{clm_data.get('reward_tokens', '0')}")
                        await countdown_timer(wait_time)
                    else:
                        error_message = clm_resp.json().get('error', 'Unknown error')
                        log(mrh + f"Failed to claim {pth}{t_id}: {error_message}")
                else:
                    error_message = cmp_resp.json().get('error', 'Unknown error')
                    log(mrh + f"Failed to complete {pth}{t_id}: {error_message}")
            else:
                log(hju + f"{tsk_type.capitalize()} {kng}task {pth}{t['task']['title']} {kng}already completed.")

    async def claim_achievements(self):
        ach_url = f"{self.b_url}/api/user/achievements/get"
        try:
            resp = self.scraper.post(ach_url, headers=self.hdrs, json={})
            if resp.status_code != 200:
                log(mrh + "Failed to retrieve achievements.")
                return
            
            achievements = resp.json()
            for category in ['friends', 'games', 'stars']:
                for achievement in achievements[category]:
                    if achievement['is_completed'] and not achievement['is_rewarded']:
                        lvl = achievement['level']
                        cl_url = f"{self.b_url}/api/user/achievements/claim"
                        pl = {"type": category, "level": lvl}
                        claim_resp = self.scraper.post(cl_url, headers=self.hdrs, json=pl)
                        if claim_resp.status_code == 200:
                            rwd_data = claim_resp.json()
                            log(hju + f"Achievement {pth}{category} {hju}level {pth}{lvl}{hju}: Reward {pth}{rwd_data['reward']}")
                        else:
                            log(mrh + f"Failed to claim {pth}{category} {mrh}achievement for level {pth}{lvl}")
                    else:
                        log(kng + "You have no achievements reward to claim")
        except Exception as e:
            log(mrh + f"An error occurred while processing achievements: {htm}{e}")

async def ld_accs(fp):
    with open(fp, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def ld_prx(fp):
    with open(fp, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def main():
    tgt_score = random.randint(45, 70)
    use_prxy = cfg.get('use_proxy', False)
    ply_game = cfg.get('play_game', False)
    cpl_tsk = cfg.get('complete_task', False)
    acc_dly = cfg.get('account_delay', 5)
    cntdwn_loop = cfg.get('countdown_loop', 3800)

    prx = await ld_prx('proxies.txt') if use_prxy else []
    accs = await ld_accs("data.txt")

    async with aiohttp.ClientSession() as session:
        for idx, acc in enumerate(accs, start=1):
            log(hju + f"Processing account {pth}{idx} {hju}of {pth}{len(accs)}")
            prxy = prx[idx % len(prx)] if use_prxy and prx else None
            game = GameSession(acc, tgt_score, prxy)

            await game.start()
            if ply_game:
                await game.run_g()
            if cpl_tsk:
                await game.cpl_and_clm_tsk(tsk_type='daily')
                await game.cpl_and_clm_tsk(tsk_type='partner')
                await game.cpl_and_clm_tsk(tsk_type='default')
                await game.cpl_and_clm_tsk(tsk_type='super')
            await game.claim_achievements()

            log_line()
            await countdown_timer(acc_dly)
        await countdown_timer(cntdwn_loop)