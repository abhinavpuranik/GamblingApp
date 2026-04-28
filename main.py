from decimal import Decimal
from gambler.gambler import GamblingProfile
from bet.betting_preferences import BettingPreferences
from gambler.gambler_profile_service import GamblerProfileService

from session.session import Session
from session.session_enum import SessionStatus
from stake.stake_boundary import StakeBoundary
from stake.stake_management_service import StakeManagementService

from bet.betting_strategy import (FixedAmountStrategy, PercentageStrategy,
                               MartingaleStrategy, ReverseMartingaleStrategy,
                               FibonacciStrategy, DAlembertStrategy)
from bet.betting_session import BettingSession
from bet.betting_service import BettingService
from session.session import Session

from session.session_parameters import SessionParameters
from game.gaming_session import GamingSession
from bet.betting_strategy import MartingaleStrategy, FixedAmountStrategy

from decimal import Decimal
from session.session_parameters import SessionParameters
from game.gaming_session import GamingSession
from bet.betting_strategy import MartingaleStrategy, FixedAmountStrategy

from game.gaming_session import GameSessionManager
from session.session_parameters import SessionParameters
from bet.betting_strategy import FixedAmountStrategy, MartingaleStrategy
from decimal import Decimal
from helper.win_loss_statistics import WinLossStatistics
from helper.odds_config import OddsConfiguration, OddsType
from bet.betting_strategy import RandomOutcomeStrategy, WeightedProbabilityStrategy
from decimal import Decimal
from validation.validation import InputValidator, ValidationConfig
from decimal import Decimal
from helper.user_interface import UserInterface



def main():
    service = GamblerProfileService()

    print("\n" + "="*50)
    print("  USE CASE 6: INPUT VALIDATION")
    print("="*50)

    print("\n" + "="*50)
    print("  USE CASE 1: CREATE GAMBLER")
    print("="*50)

    validator = InputValidator(ValidationConfig())


    valid_stake = Decimal("500.00")
    res = validator.validate_initial_stake(valid_stake)
    print(f"\nValid Stake Test (${valid_stake}) → {res.summary()}")

   
    invalid_stake = Decimal("-100.00")
    res = validator.validate_initial_stake(invalid_stake)
    print(f"\nNegative Stake Test ({invalid_stake}) → {res.summary()}")

#
    zero_stake = Decimal("0.00")
    res = validator.validate_initial_stake(zero_stake)
    print(f"\nZero Stake Test (${zero_stake}) → {res.summary()}")


    huge_stake = Decimal("999999999.00")
    res = validator.validate_initial_stake(huge_stake)
    print(f"\nHuge Stake Test (${huge_stake}) → {res.summary()}")


    gambler = service.create_gambler(
        username="abhinav99",
        full_name="Abhinav Kumar",
        email="abhinav@example.com",
        initial_stake=Decimal("1000.00"),
        win_threshold=Decimal("1500.00"),
        loss_threshold=Decimal("600.00"),
        min_required_stake=Decimal("100.00"),
        min_bet=Decimal("5.00"),
        max_bet=Decimal("100.00"),
        preferred_game_type="SLOTS",
        auto_play_enabled=True,
        auto_play_max_games=50,
        session_loss_limit=Decimal("200.00"),
        session_win_target=Decimal("300.00")
    )

   
    gambler.record_win(Decimal("80.00"))
    gambler.record_win(Decimal("40.00"))
    gambler.record_loss(Decimal("30.00"))
    gambler.record_loss(Decimal("50.00"))
    gambler.record_win(Decimal("60.00"))
    gambler.update_stake_and_stats()

    print("\n" + "="*50)
    print("  USE CASE 2: UPDATE GAMBLER")
    print("="*50)

  
    service.update_personal_info(
        gambler,
        new_full_name="Abhinav K.",
        new_email="abhinav.new@example.com"
    )


    service.update_thresholds(
        gambler,
        new_win_threshold=Decimal("1600.00"),
        new_loss_threshold=Decimal("550.00")
    )


    prefs_row = BettingPreferences.find_by_gambler(gambler.gambler_id)
   
    prefs = BettingPreferences(
        gambler_id=prefs_row["gambler_id"],
        min_bet=Decimal(str(prefs_row["min_bet"])),
        max_bet=Decimal(str(prefs_row["max_bet"])),
        preferred_game_type=prefs_row["preferred_game_type"],
        auto_play_enabled=prefs_row["auto_play_enabled"],
        auto_play_max_games=prefs_row["auto_play_max_games"],
        session_loss_limit=Decimal(str(prefs_row["session_loss_limit"])),
        session_win_target=Decimal(str(prefs_row["session_win_target"]))
    )
    prefs.preference_id = prefs_row["preference_id"]

    service.update_preferences(
        prefs,
        max_bet=Decimal("150.00"),
        preferred_game_type="POKER",
        auto_play_enabled=False
    )

    print("\n" + "="*50)
    print("  USE CASE 3: RETRIEVE STATISTICS")
    print("="*50)

    stats = service.get_statistics(gambler.gambler_id)
    print(stats.summary())

    print("\n" + "="*50)
    print("  USE CASE 4: VALIDATE ELIGIBILITY")
    print("="*50)

    result = service.validate_eligibility(gambler.gambler_id)
    print(f"  Eligible : {result['is_eligible']}")
    if result["reasons"]:
        for r in result["reasons"]:
            print(f"  Reason   : {r}")

    # force a threshold breach to show ineligibility
    print("\n  -- Simulating loss threshold breach --")
    gambler.record_loss(Decimal("600.00"))
    gambler.update_stake_and_stats()
    result2 = service.validate_eligibility(gambler.gambler_id)
    print(f"  Eligible : {result2['is_eligible']}")
    for r in result2["reasons"]:
        print(f"  Reason   : {r}")

    print("\n" + "="*50)
    print("  USE CASE 5: RESET PROFILE")
    print("="*50)

    service.reset_profile(gambler, new_initial_stake=Decimal("800.00"))

    
    stats_after_reset = service.get_statistics(gambler.gambler_id)
    print(stats_after_reset.summary())

    print("\n" + "="*50)
    print("  USE CASE 2: STAKE MANAGEMENT")
    print("="*50)

    stake_service = StakeManagementService()

    session = Session(
        gambler_id=gambler.gambler_id,
        starting_stake=gambler.current_stake,
        max_games=20
    )
    session.save()

    boundary = StakeBoundary(
        lower_limit=Decimal("100.00"),
        upper_limit=Decimal("2000.00")
    )

   
    stake_service.initialize_stake(
        gambler_id=gambler.gambler_id,
        session_id=session.session_id,
        initial_stake=gambler.current_stake,
        boundary=boundary
    )


    stake_service.deposit(gambler.gambler_id, session.session_id,
                          Decimal("200.00"), boundary)
    print(f"  Live balance: ${stake_service.get_current_balance(session.session_id)}")

    fake_bet_id = "bet-demo-001"
    stake_service.process_bet_placed(gambler.gambler_id, session.session_id,
                                     fake_bet_id, Decimal("50.00"))
    stake_service.process_bet_win(gambler.gambler_id, session.session_id,
                                  fake_bet_id, Decimal("95.00"))

    fake_bet_id_2 = "bet-demo-002"
    stake_service.process_bet_placed(gambler.gambler_id, session.session_id,
                                     fake_bet_id_2, Decimal("30.00"))
    stake_service.process_bet_loss(gambler.gambler_id, session.session_id,
                                   fake_bet_id_2, Decimal("30.00"))

    analysis = stake_service.get_fluctuation_analysis(session.session_id)
    print(f"\n  Fluctuation Analysis:")
    for k, v in analysis.items():
        print(f"    {k:<20}: {v}")

    
    print(f"\n  Boundary Validation:")
    result = stake_service.validate_stake(session.session_id, boundary)
    print(f"    is_valid : {result['is_valid']}")
    print(f"    warnings : {result['warnings']}")

   
    report = stake_service.generate_report(gambler.gambler_id, session.session_id)
    print(report.summary())

    print("\n" + "="*52)
    print("  USE CASE 3: BETTING MECHANISM")
    print("="*52)

    svc = BettingService()

    db_session = Session(
        gambler_id=gambler.gambler_id,
        starting_stake=gambler.current_stake,
        max_games=30
    )
    db_session.save()

    print("\n-- Single Bet --")
    bs = BettingSession(db_session.session_id,
                        gambler.gambler_id,
                        gambler.current_stake)

    bet = svc.place_bet(
        bs, gambler.gambler_id,
        bet_amount=Decimal("50.00"),
        win_probability=Decimal("0.45"),
        odds_type="FIXED",
        odds_value=Decimal("1.90")
    )
    svc.determine_outcome(bet)
    svc.settle_bet(bet, bs)

    print("\n-- Bet Validation --")
    result = svc.validate_bet_amount(
        amount=Decimal("5000.00"),
        current_stake=gambler.current_stake,
        min_bet=Decimal("5.00"),
        max_bet=Decimal("200.00")
    )
    print(f"  Valid: {result['is_valid']} | Errors: {result['errors']}")


    print("\n-- Strategy Bets --")
    strategies = [
        FixedAmountStrategy(Decimal("20.00")),
        PercentageStrategy(Decimal("5")),
        MartingaleStrategy(Decimal("10.00")),
        ReverseMartingaleStrategy(Decimal("10.00")),
        FibonacciStrategy(Decimal("10.00")),
        DAlembertStrategy(Decimal("10.00")),
    ]
    for strategy in strategies:
        try:
            b = svc.place_bet_with_strategy(
                bs, gambler.gambler_id, strategy,
                win_probability=Decimal("0.45"),
                odds_type="FIXED",
                odds_value=Decimal("1.90"),
                min_bet=Decimal("5.00"),
                max_bet=Decimal("200.00")
            )
            svc.determine_outcome(b)
            svc.settle_bet(b, bs)
        except ValueError as e:
            print(f"  [{strategy.__class__.__name__}] skipped — {e}")


    print("\n-- Consecutive Bets (Martingale x10) --")
    bs2 = BettingSession(db_session.session_id,
                         gambler.gambler_id,
                         gambler.current_stake)
    martingale = MartingaleStrategy(Decimal("10.00"))
    svc.place_consecutive_bets(
        bs2, gambler.gambler_id, martingale,
        num_bets=10,
        win_probability=Decimal("0.45"),
        odds_type="FIXED",
        odds_value=Decimal("1.90"),
        min_bet=Decimal("5.00"),
        max_bet=Decimal("500.00")
    )
    bs2.print_summary()

    print("\n" + "="*55)
    print("  USE CASE 4: SESSION MANAGEMENT — GamingSession")
    print("="*55)


    params = SessionParameters(
        session_id="placeholder",          
        lower_limit=Decimal("300.00"),
        upper_limit=Decimal("2000.00"),
        min_bet=Decimal("5.00"),
        max_bet=Decimal("100.00"),
        default_win_probability=Decimal("0.45"),
        max_session_minutes=60,
        maximum_games=10,
        strict_mode=False
    )

    gs = GamingSession(
        gambler_id=gambler.gambler_id,
        params=params,
        starting_stake=Decimal("1000.00")
    )

    
    gs.start()

    
    strategy = FixedAmountStrategy(Decimal("30.00"))
    for _ in range(3):
        if gs.status.value == "ACTIVE":
            gs.play_game(strategy)

  
    gs.pause("Comfort break")
    import time; time.sleep(1)
    gs.resume()

 
    martingale = MartingaleStrategy(Decimal("10.00"))
    for _ in range(3):
        if gs.status.value == "ACTIVE":
            gs.play_game(martingale)


    if gs.status.value == "ACTIVE":
        gs.end_manually()

    gs.print_summary()

    print("\n" + "="*55)
    print("  USE CASE 4-6: GAME SESSION MANAGER")
    print("="*55)

    manager = GameSessionManager()

    params = SessionParameters(
        session_id="placeholder",
        lower_limit=Decimal("200.00"),
        upper_limit=Decimal("2000.00"),
        min_bet=Decimal("5.00"),
        max_bet=Decimal("100.00"),
        default_win_probability=Decimal("0.45"),
        max_session_minutes=60,
        maximum_games=8,
        strict_mode=False
    )


    manager.start_session(gambler.gambler_id, params, Decimal("1000.00"))

    try:
        manager.start_session(gambler.gambler_id, params, Decimal("500.00"))
    except Exception as e:
        print(f"[EXPECTED ERROR] {e}")


    strategy = FixedAmountStrategy(Decimal("40.00"))
    for _ in range(4):
        if manager.has_active_session(gambler.gambler_id):
            manager.play_game(gambler.gambler_id, strategy)

    if manager.has_active_session(gambler.gambler_id):
        manager.pause_session(gambler.gambler_id, "short break")
        manager.resume_session(gambler.gambler_id)


    print("\n  -- Live Report --")
    manager.print_all_active()
    report = manager.get_active_session_report(gambler.gambler_id)
    print(f"  Games played : {report['games_played']}")
    print(f"  Current stake: ${report['current_stake']}")


    if manager.has_active_session(gambler.gambler_id):
        manager.end_session(gambler.gambler_id)


    manager.start_session(gambler.gambler_id, params, Decimal("800.00"))
    martingale = MartingaleStrategy(Decimal("10.00"))
    while manager.has_active_session(gambler.gambler_id):
        manager.play_game(gambler.gambler_id, martingale)


    manager.print_gambler_summary(gambler.gambler_id)

    print("\n" + "="*55)
    print("  USE CASE 5: WIN/LOSS CALCULATION")
    print("="*55)

   
    print("\n-- Odds Configuration Examples --")
    bet_amount = Decimal("50.00")
    configs = [
        OddsConfiguration(OddsType.FIXED,             Decimal("1.90")),
        OddsConfiguration(OddsType.DECIMAL,            Decimal("2.10")),
        OddsConfiguration(OddsType.AMERICAN,           Decimal("150")),
        OddsConfiguration(OddsType.AMERICAN,           Decimal("-110")),
        OddsConfiguration(OddsType.PROBABILITY_BASED,  Decimal("0.45")),
    ]
    for cfg in configs:
        payout = cfg.calculate_potential_win(bet_amount)
        print(f"  {cfg.describe():<35} → payout: ${payout}")


    print("\n-- Session with WeightedProbabilityStrategy (3% house edge) --")
    params2 = SessionParameters(
        session_id="placeholder",
        lower_limit=Decimal("100.00"),
        upper_limit=Decimal("3000.00"),
        min_bet=Decimal("5.00"),
        max_bet=Decimal("100.00"),
        default_win_probability=Decimal("0.48"),
        max_session_minutes=60,
        maximum_games=20,
        strict_mode=False
    )
    gs2 = GamingSession(
        gambler_id=gambler.gambler_id,
        params=params2,
        starting_stake=Decimal("1000.00")
    )
    gs2.set_outcome_strategy(WeightedProbabilityStrategy(Decimal("0.03")))
    gs2.start()

    ui = UserInterface()

    strategy = FixedAmountStrategy(Decimal("20.00"))

    while gs.status.value == "ACTIVE":

        choice = ui.display_main_menu()

        if choice == "1":
            ui.display_current_status(gs)

            bet_amount = ui.prompt_for_bet_amount()

            try:
      
                strategy.fixed_amount = bet_amount

                record = gs.play_game(strategy)
                ui.display_game_outcome(record)

            except Exception as e:
                print(f"❌ Error: {e}")

        elif choice == "2":
            ui.display_current_status(gs)

        elif choice == "3":
            gs.end_manually()
            break

        else:
            print("❌ Invalid option")

    fixed_strategy = FixedAmountStrategy(Decimal("25.00"))
    while gs2.status == SessionStatus.ACTIVE:
        try:
            gs2.play_game(fixed_strategy)
        except Exception:
            break

    gs2.win_loss_stats.print_summary()


if __name__ == "__main__":
    main()