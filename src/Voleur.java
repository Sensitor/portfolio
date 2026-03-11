public class Voleur extends Profil {
    public Voleur() {
        super("Voleur", 6);
    }

    @Override
    public int calculerPV(int modCon) {
        return 6 + modCon;
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag) {
        return 0;
    }
}
