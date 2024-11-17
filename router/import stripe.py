import stripe

stripe.api_key = "rk_test_51MGD2ECiScSQxo4glNmBiBx20FxMgVN23bux7jOiinhvyInEteTwkNHLyePgV7MvnoMkYlpDxWCyGpcbMIlVzBbO00WBeTTkOd"

try:
    balance = stripe.Balance.retrieve()
    print("Conexão bem-sucedida:", balance)
except stripe.error.AuthenticationError as e:
    print("Erro de autenticação:", e)
