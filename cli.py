from decimal import Decimal

from gambler.gambler import GamblingProfile
from gambler.gambler_profile_service import GamblerProfileService

from helper.user_interface import UserInterface
from game.gaming_session import GamingSession
from session.session_parameters import SessionParameters
from bet.betting_strategy import FixedAmountStrategy


def run_cli():

    ui = UserInterface()
    service = GamblerProfileService()

    print("\n" + "="*50)
    print("  CLI MODE — GAMBLING APP")
    print("="*50)

    # ✅ Get or create gambler (FIXED)
    existing = GamblingProfile.find_by_username("cli_user")

    if existing:
        print("Using existing CLI gambler")
        gambler_id = existing["gambler_id"]
    else:
        print("Creating new CLI gambler")

        gambler = service.create_gambler(
            username="cli_user",
            full_name="CLI User",
            email="cli@example.com",
            initial_stake=Decimal("1000.00"),
            win_threshold=Decimal("1500.00"),
            loss_threshold=Decimal("500.00"),
            min_required_stake=Decimal("100.00"),
            min_bet=Decimal("5.00"),
            max_bet=Decimal("100.00"),
            preferred_game_type="CLI",
            auto_play_enabled=False,
            auto_play_max_games=10,
            session_loss_limit=Decimal("200.00"),
            session_win_target=Decimal("300.00")
        )

        gambler_id = gambler.gambler_id

    print(f"Gambler ID: {gambler_id[:8]}...")

    # ✅ Session setup
    params = SessionParameters(
        session_id="cli",
        lower_limit=Decimal("100.00"),
        upper_limit=Decimal("2000.00"),
        min_bet=Decimal("5.00"),
        max_bet=Decimal("100.00"),
        default_win_probability=Decimal("0.45"),
        max_session_minutes=60,
        maximum_games=50,
        strict_mode=False
    )

    session = GamingSession(
        gambler_id=gambler_id,
        params=params,
        starting_stake=Decimal("1000.00")
    )

    session.start()

    strategy = FixedAmountStrategy(Decimal("10.00"))

    # 🔁 MAIN INTERACTIVE LOOP
    while session.status.value == "ACTIVE":

        choice = ui.display_main_menu()

        if choice == "1":
            ui.display_current_status(session)

            bet_amount = ui.prompt_for_bet_amount()

            try:
                # override strategy dynamically
                strategy.fixed_amount = bet_amount

                record = session.play_game(strategy)
                ui.display_game_outcome(record)

            except Exception as e:
                print(f"❌ Error: {e}")

        elif choice == "2":
            ui.display_current_status(session)

        elif choice == "3":
            session.end_manually()
            break

        else:
            print("❌ Invalid option")

    # ✅ Final summary
    ui.display_session_summary(session)


if __name__ == "__main__":
    run_cli()