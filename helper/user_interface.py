from decimal import Decimal

class UserInterface:


    def display_current_status(self, session):
        print("\n" + "-"*50)
        print("  CURRENT STATUS")
        print("-"*50)
        print(f"Session ID   : {session.session_id[:8]}...")
        print(f"Status       : {session.status.value}")
        print(f"Current Stake: ${session.current_stake}")
        print(f"Games Played : {session.games_played}")
        print("-"*50)


    def prompt_for_bet_amount(self):
        while True:
            try:
                value = input("Enter bet amount: $")
                bet = Decimal(value)

                if bet <= 0:
                    print("❌ Bet must be positive")
                    continue

                return bet

            except Exception:
                print("❌ Invalid input. Enter a numeric value.")


 
    def display_game_outcome(self, record):
        print("\n" + "-"*50)
        print("  GAME RESULT")
        print("-"*50)

        outcome = "WON" if record.outcome.value == "WIN" else "LOST"

        print(f"Outcome      : {outcome}")
        print(f"Bet Amount   : ${record.bet_amount}")
        print(f"Payout       : ${record.payout_amount}")
        print(f"Stake Before : ${record.stake_before}")
        print(f"Stake After  : ${record.stake_after}")
        print("-"*50)


    def display_session_summary(self, session):
        print("\n" + "="*60)
        print("  SESSION SUMMARY")
        print("="*60)

        stats = session.get_statistics()

        print(f"Final Stake  : ${stats['current_stake']}")
        print(f"Net Change   : ${stats['net_change']}")
        print(f"Games Played : {stats['games_played']}")
        print(f"Win Rate     : {stats['win_rate']}%")

        print("="*60)


 
    def display_main_menu(self):
        print("\n" + "="*40)
        print("  MAIN MENU")
        print("="*40)
        print("1. Play Game")
        print("2. View Status")
        print("3. End Session")
        print("="*40)

        return input("Choose option: ")