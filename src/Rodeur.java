public class Rodeur extends Profil {
    public Rodeur() {
        super("Rodeur", 8);
    }

    @Override
    public int calculerPV(int modCon) {
        return 8 + modCon;
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag) {
        return 0;
    }
}
