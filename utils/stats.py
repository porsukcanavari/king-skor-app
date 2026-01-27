# utils/stats.py
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime
from utils.config import OYUN_KURALLARI, STARTING_ELO, K_FACTOR, SOLO_MULTIPLIER
from utils.database import fetch_all_data, get_users_map

def calculate_expected_score(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 400))

def parse_date_from_header(header_str):
    try:
        date_str = header_str.split('(')[-1].split(')')[0].strip()
        return datetime.strptime(date_str, "%d.%m.%Y")
    except: return datetime.now()

def extract_id_from_cell(cell_value, name_to_id_map):
    if not cell_value: return None
    s = str(cell_value).strip()
    match = re.search(r'\(uid:(\d+)\)', s)
    if match: return int(match.group(1))
    clean_name = s.split('(')[0].strip()
    if clean_name in name_to_id_map: return name_to_id_map[clean_name]
    return None

def istatistikleri_hesapla():
    id_to_name, name_to_id, _ = get_users_map()
    _, raw_data = fetch_all_data()
    
    if not raw_data: return None, None, None, None
    
    player_stats = {}
    elo_ratings = {}
    all_matches_chronological = []
    match_history_display = []
    
    for uid in id_to_name.keys():
        player_stats[uid] = {
            "mac_sayisi": 0, "toplam_puan": 0, "pozitif_mac_sayisi": 0,
            "cezalar": {k: 0 for k in OYUN_KURALLARI}, "ceza_puanlari": {k: 0 for k in OYUN_KURALLARI},
            "kkd": STARTING_ELO, "win_streak": 0, "max_win_streak": 0,
            "loss_streak": 0, "max_loss_streak": 0,
            "toplam_ceza_puani": 0, "king_sayisi": 0, "king_kazanma": 0,
            "son_5_mac": [], "aylik_performans": defaultdict(lambda: {'mac': 0, 'puan': 0})
        }
        elo_ratings[uid] = STARTING_ELO
        
    current_match_data = None
    current_match_ids = []
    king_winner_id = None
    
    for row in raw_data:
        if not row or not any(row): continue
        first = str(row[0]).strip()
        
        if first.startswith("--- MAÇ:"):
            if current_match_data: all_matches_chronological.append(current_match_data)
            current_match_ids = []
            current_match_data = {
                "baslik": first, "tarih": parse_date_from_header(first),
                "skorlar": [], "ids": [], "oyun_tipi": "Normal",
                "ceza_puan_detaylari": defaultdict(lambda: defaultdict(float)),
                "kazananlar": [], "kaybedenler": []
            }
            continue
            
        if not current_match_data: continue
        
        if first == "OYUN TÜRÜ":
            for val in row[1:]:
                pid = extract_id_from_cell(val, name_to_id)
                if pid in player_stats: current_match_ids.append(pid)
            current_match_data["ids"] = current_match_ids
            continue
            
        is_king = "KING" in first.upper()
        if is_king:
            current_match_data["oyun_tipi"] = "KING"
            king_winner_id = extract_id_from_cell(first, name_to_id)
            if king_winner_id in player_stats:
                player_stats[king_winner_id]["king_sayisi"] += 1
                current_match_data["king_winner"] = king_winner_id
                
        base_name = first.split(" #")[0].split(" (")[0]
        if (base_name in OYUN_KURALLARI or is_king) and current_match_ids:
            current_match_data["skorlar"].append(row)
            for i, pid in enumerate(current_match_ids):
                if i+1 >= len(row): continue
                try:
                    score = int(row[i+1])
                    if pid in player_stats:
                        stats = player_stats[pid]
                        if not is_king and score < 0:
                            stats["toplam_ceza_puani"] += score
                            current_match_data["ceza_puan_detaylari"][pid][base_name] += score
                            stats["ceza_puanlari"][base_name] += score
                except: pass
                
        if first == "TOPLAM" and current_match_ids:
            current_match_data["toplamlar"] = row
            match_res = {}
            for i, pid in enumerate(current_match_ids):
                if i+1 >= len(row): continue
                try:
                    total = int(row[i+1])
                    match_res[pid] = total
                    
                    is_win = (total >= 0) if current_match_data["oyun_tipi"] != "KING" else (pid == king_winner_id)
                    if is_win: current_match_data["kazananlar"].append(pid)
                    else: current_match_data["kaybedenler"].append(pid)
                    
                    if pid in player_stats:
                        s = player_stats[pid]
                        s["mac_sayisi"] += 1
                        s["toplam_puan"] += total
                        if is_win: 
                            s["pozitif_mac_sayisi"] += 1
                            if current_match_data["oyun_tipi"] == "KING": s["king_kazanma"] += 1
                        
                        s["son_5_mac"].append({"tarih": current_match_data["tarih"], "puan": total, "kazandi": is_win, "tur": current_match_data["oyun_tipi"]})
                        if len(s["son_5_mac"]) > 5: s["son_5_mac"].pop(0)
                        
                        m_key = current_match_data["tarih"].strftime("%Y-%m")
                        s["aylik_performans"][m_key]["mac"] += 1
                        s["aylik_performans"][m_key]["puan"] += total
                        
                except: pass
            
            # ELO Hesaplama
            new_elos = {}
            for pid in current_match_ids:
                my_elo = elo_ratings.get(pid, STARTING_ELO)
                # Basit ELO mantığı
                actual = 1 if pid in current_match_data["kazananlar"] else 0
                opps = [elo_ratings.get(o, STARTING_ELO) for o in current_match_ids if o != pid]
                avg_opp = sum(opps) / len(opps) if opps else STARTING_ELO
                exp = 1 / (1 + 10 ** ((avg_opp - my_elo) / 400))
                change = K_FACTOR * (actual - exp)
                if (actual == 1 and len(current_match_data["kazananlar"]) == 1) or (actual == 0 and len(current_match_data["kaybedenler"]) == 1):
                    change *= SOLO_MULTIPLIER
                new_elos[pid] = round(my_elo + change)
            
            for pid, val in new_elos.items():
                elo_ratings[pid] = val
                if pid in player_stats: player_stats[pid]["kkd"] = val
                
            current_match_data["sonuclar"] = match_res
            match_history_display.append(current_match_data.copy())
            
    if current_match_data: all_matches_chronological.append(current_match_data)
    
    # Streak Hesaplama
    streak_tracker = {uid: {'w': 0, 'l': 0} for uid in id_to_name}
    for m in all_matches_chronological:
        for pid in m.get('ids', []):
            if pid not in player_stats: continue
            if pid in m.get('kazananlar', []):
                streak_tracker[pid]['w'] += 1
                streak_tracker[pid]['l'] = 0
            else:
                streak_tracker[pid]['l'] += 1
                streak_tracker[pid]['w'] = 0
            
            player_stats[pid]['max_win_streak'] = max(player_stats[pid]['max_win_streak'], streak_tracker[pid]['w'])
            player_stats[pid]['max_loss_streak'] = max(player_stats[pid]['max_loss_streak'], streak_tracker[pid]['l'])
            player_stats[pid]['win_streak'] = streak_tracker[pid]['w']
            player_stats[pid]['loss_streak'] = streak_tracker[pid]['l']

    return player_stats, match_history_display, all_matches_chronological, id_to_name